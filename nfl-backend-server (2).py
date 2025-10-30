from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Mock NFL data for testing
TEAMS_DATA = {
    'KC': {
        'name': 'Kansas City Chiefs',
        'players': {
            'QB': [{'name': 'Patrick Mahomes', 'number': 15, 'fp': 24.1}],
            'RB': [{'name': 'Isiah Pacheco', 'number': 10, 'fp': 12.4}],
            'WR': [{'name': 'Rashee Rice', 'number': 1, 'fp': 16.8}],
            'TE': [{'name': 'Travis Kelce', 'number': 87, 'fp': 14.2}]
        }
    },
    'BUF': {
        'name': 'Buffalo Bills',
        'players': {
            'QB': [{'name': 'Josh Allen', 'number': 17, 'fp': 23.5}],
            'RB': [{'name': 'James Cook', 'number': 4, 'fp': 14.8}],
            'WR': [{'name': 'Stefon Diggs', 'number': 14, 'fp': 16.8}],
            'TE': [{'name': 'Dalton Kincaid', 'number': 86, 'fp': 11.2}]
        }
    },
    'BAL': {
        'name': 'Baltimore Ravens',
        'players': {
            'QB': [{'name': 'Lamar Jackson', 'number': 8, 'fp': 25.8}],
            'RB': [{'name': 'Derrick Henry', 'number': 22, 'fp': 17.2}],
            'WR': [{'name': 'Zay Flowers', 'number': 0, 'fp': 15.5}],
            'TE': [{'name': 'Mark Andrews', 'number': 89, 'fp': 12.8}]
        }
    },
    'PHI': {
        'name': 'Philadelphia Eagles',
        'players': {
            'QB': [{'name': 'Jalen Hurts', 'number': 1, 'fp': 25.2}],
            'RB': [{'name': 'Saquon Barkley', 'number': 26, 'fp': 19.8}],
            'WR': [{'name': 'A.J. Brown', 'number': 11, 'fp': 17.5}],
            'TE': [{'name': 'Dallas Goedert', 'number': 88, 'fp': 13.5}]
        }
    },
    'SF': {
        'name': 'San Francisco 49ers',
        'players': {
            'QB': [{'name': 'Brock Purdy', 'number': 13, 'fp': 22.5}],
            'RB': [{'name': 'Christian McCaffrey', 'number': 25, 'fp': 18.5}],
            'WR': [{'name': 'Deebo Samuel', 'number': 19, 'fp': 15.2}],
            'TE': [{'name': 'George Kittle', 'number': 85, 'fp': 16.4}]
        }
    },
    'DAL': {
        'name': 'Dallas Cowboys',
        'players': {
            'QB': [{'name': 'Dak Prescott', 'number': 4, 'fp': 22.8}],
            'RB': [{'name': 'Rico Dowdle', 'number': 2, 'fp': 13.6}],
            'WR': [{'name': 'CeeDee Lamb', 'number': 88, 'fp': 18.2}],
            'TE': [{'name': 'Jake Ferguson', 'number': 87, 'fp': 12.8}]
        }
    }
}

SCHEDULE_DATA = {
    9: [
        {'week': 9, 'home_team': 'BAL', 'away_team': 'MIA', 'date': '2025-10-30'},
        {'week': 9, 'home_team': 'KC', 'away_team': 'BUF', 'date': '2025-11-02'},
        {'week': 9, 'home_team': 'DAL', 'away_team': 'ARI', 'date': '2025-11-03'},
    ]
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Backend is running'}), 200

@app.route('/api/teams', methods=['GET'])
def get_teams():
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

@app.route('/api/players/<team>', methods=['GET'])
def get_team_players(team):
    team = team.upper()
    if team not in TEAMS_DATA:
        return jsonify({'error': f'Team {team} not found'}), 404
    return jsonify(TEAMS_DATA[team]['players'])

@app.route('/api/players/<team>/<position>', methods=['GET'])
def get_position_players(team, position):
    team = team.upper()
    position = position.upper()
    
    if team not in TEAMS_DATA:
        return jsonify({'error': f'Team {team} not found'}), 404
    
    if position not in TEAMS_DATA[team]['players']:
        return jsonify({'error': f'Position {position} not found'}), 404
    
    return jsonify(TEAMS_DATA[team]['players'][position])

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    week = request.args.get('week', 9, type=int)
    if week in SCHEDULE_DATA:
        return jsonify(SCHEDULE_DATA[week])
    return jsonify([])

@app.route('/api/schedule/week/<int:week>', methods=['GET'])
def get_week_schedule(week):
    if week in SCHEDULE_DATA:
        return jsonify(SCHEDULE_DATA[week])
    return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
