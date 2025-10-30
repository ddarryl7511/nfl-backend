# NFL Data Backend Server
# Uses nflreadpy to fetch data from nflverse
# Serves REST API endpoints for the dashboard

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

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
    'last_updated': None
}

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_nfl_data():
    """Load all NFL data from nflverse"""
    try:
        from nflreadpy import load_player_stats, load_rosters, load_pbp
        
        logger.info("Loading NFL data from nflverse...")
        
        # Load player stats
        logger.info("Loading player stats...")
        player_stats = load_player_stats(2025)
        
        # Load rosters
        logger.info("Loading rosters...")
        rosters = load_rosters(2025)
        
        # Load play-by-play data for schedule/games
        logger.info("Loading play-by-play data...")
        pbp = load_pbp(2025)
        
        # Cache the data
        data_cache['player_stats'] = player_stats
        data_cache['rosters'] = rosters
        data_cache['pbp'] = pbp
        data_cache['last_updated'] = datetime.now().isoformat()
        
        logger.info("Data loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading NFL data: {str(e)}")
        return False

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'last_updated': data_cache['last_updated'],
        'data_available': data_cache['player_stats'] is not None
    })

@app.route('/api/players', methods=['GET'])
def get_all_players():
    """Get all players with stats"""
    if data_cache['player_stats'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        stats = data_cache['player_stats'].copy()
        
        # Select relevant columns
        columns = ['player_name', 'player_display_name', 'position', 'recent_team', 
                   'season', 'week', 'passing_yards', 'passing_tds', 'interceptions',
                   'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards', 
                   'receiving_tds', 'fantasy_points']
        
        # Filter to available columns
        available_cols = [col for col in columns if col in stats.columns]
        stats = stats[available_cols]
        
        # Convert to JSON-serializable format
        return jsonify(stats.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting all players: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<team>', methods=['GET'])
def get_team_players(team):
    """Get players for a specific team"""
    if data_cache['player_stats'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        team = team.upper()
        stats = data_cache['player_stats'].copy()
        
        # Filter by team
        team_players = stats[stats['recent_team'] == team]
        
        if team_players.empty:
            return jsonify({'error': f'No data found for team {team}'}), 404
        
        # Select relevant columns
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'interceptions', 
                   'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards',
                   'receiving_tds', 'fantasy_points', 'week', 'season']
        
        available_cols = [col for col in columns if col in team_players.columns]
        team_players = team_players[available_cols]
        
        return jsonify(team_players.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting team players: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/players/<team>/<position>', methods=['GET'])
def get_team_position_players(team, position):
    """Get players for a specific team and position"""
    if data_cache['player_stats'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        team = team.upper()
        position = position.upper()
        stats = data_cache['player_stats'].copy()
        
        # Filter by team and position
        players = stats[(stats['recent_team'] == team) & (stats['position'] == position)]
        
        if players.empty:
            return jsonify({'error': f'No {position} players found for team {team}'}), 404
        
        # Select relevant columns and remove duplicates
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'interceptions',
                   'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards',
                   'receiving_tds', 'fantasy_points', 'week', 'season']
        
        available_cols = [col for col in columns if col in players.columns]
        players = players[available_cols].drop_duplicates(subset=['player_name', 'week'])
        
        return jsonify(players.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting position players: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get NFL schedule/games"""
    if data_cache['pbp'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        pbp = data_cache['pbp'].copy()
        
        # Get unique games
        games = pbp[['game_id', 'home_team', 'away_team', 'game_date', 'week', 'season']].drop_duplicates()
        
        # Filter to current/recent week if week parameter provided
        week = request.args.get('week', type=int)
        if week:
            games = games[games['week'] == week]
        
        if games.empty:
            return jsonify({'error': 'No games found'}), 404
        
        return jsonify(games.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule/week/<int:week>', methods=['GET'])
def get_week_schedule(week):
    """Get schedule for specific week"""
    if data_cache['pbp'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        pbp = data_cache['pbp'].copy()
        
        # Filter by week
        games = pbp[pbp['week'] == week][['game_id', 'home_team', 'away_team', 'game_date']].drop_duplicates()
        
        if games.empty:
            return jsonify({'error': f'No games found for week {week}'}), 404
        
        return jsonify(games.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting week schedule: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rosters', methods=['GET'])
def get_rosters():
    """Get all team rosters"""
    if data_cache['rosters'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        rosters = data_cache['rosters'].copy()
        
        # Select relevant columns
        columns = ['player_name', 'player_id', 'position', 'team', 'depth_chart_position']
        available_cols = [col for col in columns if col in rosters.columns]
        rosters = rosters[available_cols]
        
        return jsonify(rosters.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting rosters: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rosters/<team>', methods=['GET'])
def get_team_roster(team):
    """Get roster for specific team"""
    if data_cache['rosters'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        team = team.upper()
        rosters = data_cache['rosters'].copy()
        
        # Filter by team
        team_roster = rosters[rosters['team'] == team]
        
        if team_roster.empty:
            return jsonify({'error': f'No roster found for team {team}'}), 404
        
        # Select relevant columns
        columns = ['player_name', 'player_id', 'position', 'team', 'depth_chart_position']
        available_cols = [col for col in columns if col in team_roster.columns]
        team_roster = team_roster[available_cols]
        
        return jsonify(team_roster.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting team roster: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/player-stats/<player_name>', methods=['GET'])
def get_player_stats(player_name):
    """Get stats for a specific player"""
    if data_cache['player_stats'] is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        stats = data_cache['player_stats'].copy()
        
        # Find player (case-insensitive)
        player_stats = stats[stats['player_display_name'].str.lower() == player_name.lower()]
        
        if player_stats.empty:
            return jsonify({'error': f'Player {player_name} not found'}), 404
        
        # Select relevant columns
        columns = ['player_name', 'player_display_name', 'position', 'recent_team',
                   'passing_yards', 'passing_tds', 'interceptions',
                   'rushing_yards', 'rushing_tds', 'receptions', 'receiving_yards',
                   'receiving_tds', 'fantasy_points', 'week', 'season']
        
        available_cols = [col for col in columns if col in player_stats.columns]
        player_stats = player_stats[available_cols]
        
        return jsonify(player_stats.to_dict('records'))
        
    except Exception as e:
        logger.error(f"Error getting player stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/teams', methods=['GET'])
def get_teams():
    """Get list of all NFL teams"""
    teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN',
        'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LV', 'LAC', 'LAR', 'MIA',
        'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB',
        'TEN', 'WAS'
    ]
    
    team_names = {
        'ARI': 'Arizona Cardinals',
        'ATL': 'Atlanta Falcons',
        'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills',
        'CAR': 'Carolina Panthers',
        'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals',
        'CLE': 'Cleveland Browns',
        'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos',
        'DET': 'Detroit Lions',
        'GB': 'Green Bay Packers',
        'HOU': 'Houston Texans',
        'IND': 'Indianapolis Colts',
        'JAX': 'Jacksonville Jaguars',
        'KC': 'Kansas City Chiefs',
        'LV': 'Las Vegas Raiders',
        'LAC': 'Los Angeles Chargers',
        'LAR': 'Los Angeles Rams',
        'MIA': 'Miami Dolphins',
        'MIN': 'Minnesota Vikings',
        'NE': 'New England Patriots',
        'NO': 'New Orleans Saints',
        'NYG': 'New York Giants',
        'NYJ': 'New York Jets',
        'PHI': 'Philadelphia Eagles',
        'PIT': 'Pittsburgh Steelers',
        'SF': 'San Francisco 49ers',
        'SEA': 'Seattle Seahawks',
        'TB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans',
        'WAS': 'Washington Commanders'
    }
    
    team_list = [{'abbr': team, 'name': team_names.get(team, team)} for team in teams]
    return jsonify(team_list)

# ============================================================================
# STARTUP
# ============================================================================

@app.before_request
def check_data():
    """Check if data is loaded on each request"""
    if data_cache['player_stats'] is None and request.path != '/api/health':
        # Try to load data
        load_nfl_data()

if __name__ == '__main__':
    logger.info("Starting NFL Data Backend Server...")
    
    # Load data on startup
    load_nfl_data()
    
    # Run server
    app.run(debug=True, host='0.0.0.0', port=5000)
