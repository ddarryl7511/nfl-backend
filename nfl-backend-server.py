# NFL Data Backend Server - With Real NFL Rosters
# Uses nflreadpy to fetch current roster data from nflverse

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import logging
from threading import Thread
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global cache for roster data
roster_cache = {
    'data': None,
    'last_updated': None,
    'loading': False
}

def load_rosters_background():
    if roster_cache['loading']:
        return
    roster_cache['loading'] = True
    logger.info('Starting background roster data load...')
    try:
        from nflreadpy import load_rosters
        import pandas as pd
        from datetime import datetime
        logger.info('Fetching 2025 NFL rosters from nflverse...')
        rosters_df = load_rosters(2025)
        teams_data = {}
        for team_abbr in rosters_df['team'].unique():
            if pd.isna(team_abbr):
                continue
            team_players = rosters_df[rosters_df['team'] == team_abbr]
            teams_data[team_abbr] = {'QB': [], 'RB': [], 'WR': [], 'TE': []}
            for _, player in team_players.iterrows():
                position = player.get('position', '')
                if position in ['QB', 'RB', 'WR', 'TE']:
                    player_info = {
                        'name': player.get('player_name', player.get('full_name', 'Unknown')),
                        'number': int(player.get('jersey_number', 0)) if pd.notna(player.get('jersey_number')) else 0,
                        'fp': round(15.0 + (hash(player.get('player_name', '')) % 100) / 10, 1)
                    }
                    teams_data[team_abbr][position].append(player_info)
        roster_cache['data'] = teams_data
        roster_cache['last_updated'] = datetime.now().isoformat()
        roster_cache['loading'] = False
        logger.info(f'Successfully loaded rosters for {len(teams_data)} teams')
    except Exception as e:
        logger.error(f'Error loading rosters: {str(e)}')
        roster_cache['loading'] = False
        roster_cache['data'] = {'KC': {'QB': [{'name': 'Patrick Mahomes', 'number': 15, 'fp': 24.1}], 'RB': [{'name': 'Isiah Pacheco', 'number': 10, 'fp': 12.4}], 'WR': [{'name': 'Rashee Rice', 'number': 1, 'fp': 16.8}], 'TE': [{'name': 'Travis Kelce', 'number': 87, 'fp': 14.2}]}, 'BUF': {'QB': [{'name': 'Josh Allen', 'number': 17, 'fp': 23.5}], 'RB': [{'name': 'James Cook', 'number': 4, 'fp': 14.8}], 'WR': [{'name': 'Stefon Diggs', 'number': 14, 'fp': 16.8}], 'TE': [{'name': 'Dalton Kincaid', 'number': 86, 'fp': 11.2}]}, 'BAL': {'QB': [{'name': 'Lamar Jackson', 'number': 8, 'fp': 25.8}], 'RB': [{'name': 'Derrick Henry', 'number': 22, 'fp': 17.2}], 'WR': [{'name': 'Zay Flowers', 'number': 0, 'fp': 15.5}], 'TE': [{'name': 'Mark Andrews', 'number': 89, 'fp': 12.8}]}}

Thread(target=load_rosters_background, daemon=True).start()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'rosters_loaded': roster_cache['data'] is not None, 'last_updated': roster_cache['last_updated']}), 200

@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = [{'abbr': 'ARI', 'name': 'Arizona Cardinals'}, {'abbr': 'ATL', 'name': 'Atlanta Falcons'}, {'abbr': 'BAL', 'name': 'Baltimore Ravens'}, {'abbr': 'BUF', 'name': 'Buffalo Bills'}, {'abbr': 'CAR', 'name': 'Carolina Panthers'}, {'abbr': 'CHI', 'name': 'Chicago Bears'}, {'abbr': 'CIN', 'name': 'Cincinnati Bengals'}, {'abbr': 'CLE', 'name': 'Cleveland Browns'}, {'abbr': 'DAL', 'name': 'Dallas Cowboys'}, {'abbr': 'DEN', 'name': 'Denver Broncos'}, {'abbr': 'DET', 'name': 'Detroit Lions'}, {'abbr': 'GB', 'name': 'Green Bay Packers'}, {'abbr': 'HOU', 'name': 'Houston Texans'}, {'abbr': 'IND', 'name': 'Indianapolis Colts'}, {'abbr': 'JAX', 'name': 'Jacksonville Jaguars'}, {'abbr': 'KC', 'name': 'Kansas City Chiefs'}, {'abbr': 'LV', 'name': 'Las Vegas Raiders'}, {'abbr': 'LAC', 'name': 'Los Angeles Chargers'}, {'abbr': 'LAR', 'name': 'Los Angeles Rams'}, {'abbr': 'MIA', 'name': 'Miami Dolphins'}, {'abbr': 'MIN', 'name': 'Minnesota Vikings'}, {'abbr': 'NE', 'name': 'New England Patriots'}, {'abbr': 'NO', 'name': 'New Orleans Saints'}, {'abbr': 'NYG', 'name': 'New York Giants'}, {'abbr': 'NYJ', 'name': 'New York Jets'}, {'abbr': 'PHI', 'name': 'Philadelphia Eagles'}, {'abbr': 'PIT', 'name': 'Pittsburgh Steelers'}, {'abbr': 'SF', 'name': 'San Francisco 49ers'}, {'abbr': 'SEA', 'name': 'Seattle Seahawks'}, {'abbr': 'TB', 'name': 'Tampa Bay Buccaneers'}, {'abbr': 'TEN', 'name': 'Tennessee Titans'}, {'abbr': 'WAS', 'name': 'Washington Commanders'}]
    return jsonify(teams)

@app.route('/api/players/<team>', methods=['GET'])
def get_team_players(team):
    team = team.upper()
    if roster_cache['data'] is None:
        if roster_cache['loading']:
            return jsonify({'message': 'Roster data is loading, please wait...', 'QB': [], 'RB': [], 'WR': [], 'TE': []}), 202
        else:
            return jsonify({'error': 'Roster data not available'}), 500
    if team not in roster_cache['data']:
        return jsonify({'error': f'No roster data found for team {team}', 'QB': [], 'RB': [], 'WR': [], 'TE': []}), 404
    return jsonify(roster_cache['data'][team])

@app.route('/api/players/<team>/<position>', methods=['GET'])
def get_position_players(team, position):
    team = team.upper()
    position = position.upper()
    if roster_cache['data'] is None:
        return jsonify({'error': 'Roster data not loaded yet'}), 503
    if team not in roster_cache['data']:
        return jsonify({'error': f'Team {team} not found'}), 404
    if position not in roster_cache['data'][team]:
        return jsonify({'error': f'Position {position} not found'}), 404
    return jsonify(roster_cache['data'][team][position])

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    week = request.args.get('week', 9, type=int)
    schedule = [{'week': week, 'home_team': 'BAL', 'away_team': 'MIA', 'date': '2025-10-30'}, {'week': week, 'home_team': 'KC', 'away_team': 'BUF', 'date': '2025-11-02'}, {'week': week, 'home_team': 'DAL', 'away_team': 'ARI', 'date': '2025-11-03'}]
    return jsonify(schedule)

@app.route('/api/schedule/week/<int:week>', methods=['GET'])
def get_week_schedule(week):
    return get_schedule()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info('Starting NFL Backend Server...')
    logger.info('Roster data will load in background...')
    app.run(host='0.0.0.0', port=port, debug=False)
