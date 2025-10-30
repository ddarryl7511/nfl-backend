# NFL Data Backend Server - Lightweight Version
# Uses nflreadpy to fetch data from nflverse
# Optimized for Railway deployment

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global cache for data
data_cache = {
    'player_stats': None,
    'rosters': None,
    'pbp': None,
    'last_updated': None,
    'loading': False
}

# ============================================================================
# BACKGROUND DATA LOADING (Non-blocking)
# ============================================================================

def load_nfl_data_async():
    """Load NFL data in background without blocking startup"""
    if data_cache['loading']:
        return
    
    data_cache['loading'] = True
    
    try:
        logger.info("Starting background data load...")
        from nflreadpy import load_player_stats, load_rosters, load_pbp
        
        # Load player stats
        logger.info("Loading player stats (this may take 1-2 minutes)...")
        player_stats = load_player_stats(2025)
        data_cache['player_stats'] = player_stats
        logger.info("✓ Player stats loaded")
        
        # Load rosters
        logger.info("Loading rosters...")
        rosters = load_rosters(2025)
        data_cache['rosters'] = rosters
        logger.info("✓ Rosters loaded")
        
        # Load play-by-play data
        logger.info("Loading schedule data...")
        pbp = load_pbp(2025)
        data_cache['pbp'] = pbp
        logger.info("✓ Schedule loaded")
        
        data_cache['last_updated'] = datetime.now().isoformat()
        data_cache['loading'] = False
        logger.info("✓ All data loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        data_cache['loading'] = False

# Start loading data in background thread
loading_thread = threading.Thread(target=load_nfl_data_async, daemon=True)
loading_thread.start()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'loading': data_cache['loading'],
        'last_updated': data_cache['last_updated'],
        'data_available': data_cache['player_stats'] is not None
    })

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of all NFL teams"""
    teams = [
        {'abbr': 'ARI', 'name': 'Arizona Cardinals'},
        {'abbr': 'ATL', 'name': 'Atlanta Falcons'},
        {'abbr': 'BAL', 'name': 'Baltimore Ravens'},
        {'abbr': 'BUF', 'name': 'Buffalo Bills'},
        {'abbr': 'CAR', 'name': 'Carolina Panthers'},
        {'abbr': 'CHI', 'name': 'Chicago Bears'},
        {'abbr': 'CIN', 'name': 'Cincinnati Bengals'},
        {'abbr': 'CLE', 'name': 'Cleveland Browns'},
        {'abbr': 'DAL', 'name': 'Dallas Cowboys'},
        {'abbr': 'DEN', 'name': 'Denver Broncos'},
        {'abbr': 'DET', 'name': 'Detroit Lions'},
        {'abbr': 'GB', 'name': 'Green Bay Packers'},
        {'abbr': 'HOU', 'name': 'Houston Texans'},
        {'abbr': 'IND', 'name': 'Indianapolis Colts'},
        {'abbr': 'JAX', 'name': 'Jacksonville Jaguars'},
        {'abbr': 'KC', 'name': 'Kansas City Chiefs'},
        {'abbr': 'LV', 'name': 'Las Vegas Raiders'},
        {'abbr': 'LAC', 'name': 'Los Angeles Chargers'},
        {'abbr': 'LAR', 'name': 'Los Angeles Rams'},
        {'abbr': 'MIA', 'name': 'Miami Dolphins'},
        {'abbr': 'MIN', 'name': 'Minnesota Vikings'},
        {'abbr': 'NE', 'name': 'New England Patriots'},
        {'abbr': 'NO', 'name': 'New Orleans Saints'},
        {'abbr': 'NYG', 'name': 'New York Giants'},
        {'abbr': 'NYJ', 'name': 'New York Jets'},
        {'abbr': 'PHI', 'name': 'Philadelphia Eagles'},
        {'abbr': 'PIT', 'name': 'Pittsburgh Steelers'},
        {'abbr': 'SF', 'name': 'San Francisco 49ers'},
        {'abbr': 'SEA', 'name': 'Seattle Seahawks'},
        {'abbr': 'TB', 'name': 'Tampa Bay Buccaneers'},
        {'abbr': 'TEN', 'name': 'Tennessee Titans'},
        {'abbr': 'WAS', 'name': 'Washington Commanders'}
    ]
    return jsonify(teams)

@app.route('/api/players', methods=['GET'])
def get_all_players():
    """Get all players with stats"""
    if data_cache['player_stats'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        stats = data_cache['player_stats'].copy()
        columns = ['player_name', 'player_display_name', 'position', 'recent_team', 
                   'passing_yards', 'passing_tds', 'interceptions',
                   'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards', 
                   'receiving_tds', 'fantasy_points', 'week']
        
        available_cols = [col for col in columns if col in stats.columns]
        stats = stats[available_cols].head(500)  # Limit response size
        
        return jsonify(stats.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<team>', methods=['GET'])
def get_team_players(team):
    """Get players for a specific team"""
    if data_cache['player_stats'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        team = team.upper()
        stats = data_cache['player_stats'].copy()
        team_players = stats[stats['recent_team'] == team]
        
        if team_players.empty:
            return jsonify({'error': f'No data for team {team}'}), 404
        
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds',
                   'receptions', 'receiving_yards', 'receiving_tds', 'fantasy_points', 'week']
        
        available_cols = [col for col in columns if col in team_players.columns]
        team_players = team_players[available_cols]
        
        return jsonify(team_players.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<team>/<position>', methods=['GET'])
def get_team_position_players(team, position):
    """Get players for a specific team and position"""
    if data_cache['player_stats'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        team = team.upper()
        position = position.upper()
        stats = data_cache['player_stats'].copy()
        
        players = stats[(stats['recent_team'] == team) & (stats['position'] == position)]
        
        if players.empty:
            return jsonify({'error': f'No {position} players for {team}'}), 404
        
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds',
                   'receptions', 'receiving_yards', 'receiving_tds', 'fantasy_points', 'week']
        
        available_cols = [col for col in columns if col in players.columns]
        players = players[available_cols].drop_duplicates(subset=['player_name'])
        
        return jsonify(players.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get NFL schedule/games"""
    if data_cache['pbp'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        pbp = data_cache['pbp'].copy()
        games = pbp[['game_id', 'home_team', 'away_team', 'game_date', 'week']].drop_duplicates()
        
        week = request.args.get('week', type=int)
        if week:
            games = games[games['week'] == week]
        
        if games.empty:
            return jsonify({'error': 'No games found'}), 404
        
        return jsonify(games.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/week/<int:week>', methods=['GET'])
def get_week_schedule(week):
    """Get schedule for specific week"""
    if data_cache['pbp'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        pbp = data_cache['pbp'].copy()
        games = pbp[pbp['week'] == week][['game_id', 'home_team', 'away_team', 'game_date']].drop_duplicates()
        
        if games.empty:
            return jsonify({'error': f'No games for week {week}'}), 404
        
        return jsonify(games.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/player-stats/<player_name>', methods=['GET'])
def get_player_stats(player_name):
    """Get stats for a specific player"""
    if data_cache['player_stats'] is None:
        return jsonify({
            'error': 'Data still loading. Check /api/health',
            'status': 'loading'
        }), 202
    
    try:
        stats = data_cache['player_stats'].copy()
        player_stats = stats[stats['player_display_name'].str.lower() == player_name.lower()]
        
        if player_stats.empty:
            return jsonify({'error': f'Player {player_name} not found'}), 404
        
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds',
                   'receptions', 'receiving_yards', 'receiving_tds', 'fantasy_points', 'week']
        
        available_cols = [col for col in columns if col in player_stats.columns]
        player_stats = player_stats[available_cols]
        
        return jsonify(player_stats.to_dict('records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting NFL Data Backend Server...")
    logger.info("Data loading in background - endpoints available immediately")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
