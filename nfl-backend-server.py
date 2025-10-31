from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

TEAMS_DATA = {
    'KC': {'name': 'Kansas City Chiefs', 'players': {'QB': [{'name': 'Patrick Mahomes', 'number': 15, 'fp': 24.1}], 'RB': [{'name': 'Isiah Pacheco', 'number': 10, 'fp': 12.4}], 'WR': [{'name': 'Rashee Rice', 'number': 1, 'fp': 16.8}], 'TE': [{'name': 'Travis Kelce', 'number': 87, 'fp': 14.2}]}},
    'BUF': {'name': 'Buffalo Bills', 'players': {'QB': [{'name': 'Josh Allen', 'number': 17, 'fp': 23.5}], 'RB': [{'name': 'James Cook', 'number': 4, 'fp': 14.8}], 'WR': [{'name': 'Stefon Diggs', 'number': 14, 'fp': 16.8}], 'TE': [{'name': 'Dalton Kincaid', 'number': 86, 'fp': 11.2}]}},
    'BAL': {'name': 'Baltimore Ravens', 'players': {'QB': [{'name': 'Lamar Jackson', 'number': 8, 'fp': 25.8}], 'RB': [{'name': 'Derrick Henry', 'number': 22, 'fp': 17.2}], 'WR': [{'name': 'Zay Flowers', 'number': 0, 'fp': 15.5}], 'TE': [{'name': 'Mark Andrews', 'number': 89, 'fp': 12.8}]}}
}

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/teams', methods=['GET'])
def get_teams():
    return jsonify([{'abbr': k, 'name': v['name']} for k, v in TEAMS_DATA.items()])

@app.route('/api/players/<team>', methods=['GET'])
def get_team_players(team):
    if team.upper() not in TEAMS_DATA:
        return jsonify({'error': 'Team not found'}), 404
    return jsonify(TEAMS_DATA[team.upper()]['players'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
