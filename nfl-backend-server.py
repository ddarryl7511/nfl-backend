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

roster_cache = {'data': None, 'last_updated': None, 'loading': False}

def get_fallback_data():
    return {'ARI': {'QB': [{'name': 'Kyler Murray', 'number': 1, 'fp': 21.3}], 'RB': [{'name': 'James Conner', 'number': 6, 'fp': 14.5}], 'WR': [{'name': 'Marvin Harrison Jr.', 'number': 18, 'fp': 15.2}], 'TE': [{'name': 'Trey McBride', 'number': 85, 'fp': 12.8}]}, 'ATL': {'QB': [{'name': 'Kirk Cousins', 'number': 18, 'fp': 22.1}], 'RB': [{'name': 'Bijan Robinson', 'number': 7, 'fp': 17.3}], 'WR': [{'name': 'Drake London', 'number': 5, 'fp': 14.8}], 'TE': [{'name': 'Kyle Pitts', 'number': 8, 'fp': 11.5}]}, 'BAL': {'QB': [{'name': 'Lamar Jackson', 'number': 8, 'fp': 25.8}], 'RB': [{'name': 'Derrick Henry', 'number': 22, 'fp': 17.2}], 'WR': [{'name': 'Zay Flowers', 'number': 4, 'fp': 15.5}], 'TE': [{'name': 'Mark Andrews', 'number': 89, 'fp': 12.8}]}, 'BUF': {'QB': [{'name': 'Josh Allen', 'number': 17, 'fp': 23.5}], 'RB': [{'name': 'James Cook', 'number': 4, 'fp': 14.8}], 'WR': [{'name': 'Khalil Shakir', 'number': 10, 'fp': 13.2}], 'TE': [{'name': 'Dalton Kincaid', 'number': 86, 'fp': 11.2}]}, 'CAR': {'QB': [{'name': 'Bryce Young', 'number': 9, 'fp': 18.4}], 'RB': [{'name': 'Chuba Hubbard', 'number': 30, 'fp': 12.6}], 'WR': [{'name': 'Adam Thielen', 'number': 19, 'fp': 11.8}], 'TE': [{'name': 'Tommy Tremble', 'number': 82, 'fp': 8.5}]}, 'CHI': {'QB': [{'name': 'Caleb Williams', 'number': 18, 'fp': 20.7}], 'RB': [{'name': "D'Andre Swift", 'number': 4, 'fp': 13.5}], 'WR': [{'name': 'DJ Moore', 'number': 2, 'fp': 15.3}], 'TE': [{'name': 'Cole Kmet', 'number': 85, 'fp': 10.8}]}, 'CIN': {'QB': [{'name': 'Joe Burrow', 'number': 9, 'fp': 24.2}], 'RB': [{'name': 'Chase Brown', 'number': 30, 'fp': 12.8}], 'WR': [{'name': "Ja'Marr Chase", 'number': 1, 'fp': 19.5}], 'TE': [{'name': 'Mike Gesicki', 'number': 88, 'fp': 9.7}]}, 'CLE': {'QB': [{'name': 'Deshaun Watson', 'number': 4, 'fp': 19.3}], 'RB': [{'name': 'Nick Chubb', 'number': 24, 'fp': 15.2}], 'WR': [{'name': 'Amari Cooper', 'number': 2, 'fp': 14.6}], 'TE': [{'name': 'David Njoku', 'number': 85, 'fp': 11.3}]}, 'DAL': {'QB': [{'name': 'Dak Prescott', 'number': 4, 'fp': 22.8}], 'RB': [{'name': 'Rico Dowdle', 'number': 23, 'fp': 11.4}], 'WR': [{'name': 'CeeDee Lamb', 'number': 88, 'fp': 18.2}], 'TE': [{'name': 'Jake Ferguson', 'number': 87, 'fp': 12.8}]}, 'DEN': {'QB': [{'name': 'Bo Nix', 'number': 10, 'fp': 20.5}], 'RB': [{'name': 'Javonte Williams', 'number': 33, 'fp': 11.8}], 'WR': [{'name': 'Courtland Sutton', 'number': 14, 'fp': 13.7}], 'TE': [{'name': 'Adam Trautman', 'number': 82, 'fp': 8.9}]}, 'DET': {'QB': [{'name': 'Jared Goff', 'number': 16, 'fp': 23.4}], 'RB': [{'name': 'Jahmyr Gibbs', 'number': 26, 'fp': 16.8}], 'WR': [{'name': 'Amon-Ra St. Brown', 'number': 14, 'fp': 17.6}], 'TE': [{'name': 'Sam LaPorta', 'number': 87, 'fp': 13.9}]}, 'GB': {'QB': [{'name': 'Jordan Love', 'number': 10, 'fp': 22.9}], 'RB': [{'name': 'Josh Jacobs', 'number': 8, 'fp': 15.3}], 'WR': [{'name': 'Jayden Reed', 'number': 11, 'fp': 14.5}], 'TE': [{'name': 'Tucker Kraft', 'number': 85, 'fp': 10.2}]}, 'HOU': {'QB': [{'name': 'C.J. Stroud', 'number': 7, 'fp': 23.7}], 'RB': [{'name': 'Joe Mixon', 'number': 28, 'fp': 16.2}], 'WR': [{'name': 'Nico Collins', 'number': 12, 'fp': 16.8}], 'TE': [{'name': 'Dalton Schultz', 'number': 86, 'fp': 10.5}]}, 'IND': {'QB': [{'name': 'Anthony Richardson', 'number': 5, 'fp': 21.2}], 'RB': [{'name': 'Jonathan Taylor', 'number': 28, 'fp': 16.5}], 'WR': [{'name': 'Michael Pittman Jr.', 'number': 11, 'fp': 14.3}], 'TE': [{'name': 'Kylen Granson', 'number': 83, 'fp': 9.2}]}, 'JAX': {'QB': [{'name': 'Trevor Lawrence', 'number': 16, 'fp': 21.8}], 'RB': [{'name': 'Travis Etienne Jr.', 'number': 1, 'fp': 14.7}], 'WR': [{'name': 'Brian Thomas Jr.', 'number': 7, 'fp': 13.9}], 'TE': [{'name': 'Evan Engram', 'number': 17, 'fp': 11.6}]}, 'KC': {'QB': [{'name': 'Patrick Mahomes', 'number': 15, 'fp': 24.1}], 'RB': [{'name': 'Isiah Pacheco', 'number': 10, 'fp': 12.4}], 'WR': [{'name': 'Xavier Worthy', 'number': 1, 'fp': 13.8}], 'TE': [{'name': 'Travis Kelce', 'number': 87, 'fp': 14.2}]}, 'LV': {'QB': [{'name': 'Gardner Minshew', 'number': 15, 'fp': 18.3}], 'RB': [{'name': 'Alexander Mattison', 'number': 22, 'fp': 10.8}], 'WR': [{'name': 'Jakobi Meyers', 'number': 16, 'fp': 12.7}], 'TE': [{'name': 'Brock Bowers', 'number': 89, 'fp': 13.5}]}, 'LAC': {'QB': [{'name': 'Justin Herbert', 'number': 10, 'fp': 22.6}], 'RB': [{'name': 'J.K. Dobbins', 'number': 27, 'fp': 14.3}], 'WR': [{'name': 'Ladd McConkey', 'number': 15, 'fp': 13.8}], 'TE': [{'name': 'Will Dissly', 'number': 81, 'fp': 9.4}]}, 'LAR': {'QB': [{'name': 'Matthew Stafford', 'number': 9, 'fp': 21.4}], 'RB': [{'name': 'Kyren Williams', 'number': 23, 'fp': 15.7}], 'WR': [{'name': 'Cooper Kupp', 'number': 10, 'fp': 16.2}], 'TE': [{'name': 'Colby Parkinson', 'number': 48, 'fp': 10.1}]}, 'MIA': {'QB': [{'name': 'Tua Tagovailoa', 'number': 1, 'fp': 23.3}], 'RB': [{'name': "De'Von Achane", 'number': 28, 'fp': 15.9}], 'WR': [{'name': 'Tyreek Hill', 'number': 10, 'fp': 18.4}], 'TE': [{'name': 'Jonnu Smith', 'number': 9, 'fp': 10.7}]}, 'MIN': {'QB': [{'name': 'Sam Darnold', 'number': 14, 'fp': 22.1}], 'RB': [{'name': 'Aaron Jones', 'number': 33, 'fp': 15.2}], 'WR': [{'name': 'Justin Jefferson', 'number': 18, 'fp': 19.3}], 'TE': [{'name': 'T.J. Hockenson', 'number': 87, 'fp': 12.4}]}, 'NE': {'QB': [{'name': 'Drake Maye', 'number': 10, 'fp': 19.8}], 'RB': [{'name': 'Rhamondre Stevenson', 'number': 38, 'fp': 13.2}], 'WR': [{'name': 'DeMario Douglas', 'number': 3, 'fp': 11.5}], 'TE': [{'name': 'Hunter Henry', 'number': 85, 'fp': 10.3}]}, 'NO': {'QB': [{'name': 'Derek Carr', 'number': 4, 'fp': 20.4}], 'RB': [{'name': 'Alvin Kamara', 'number': 41, 'fp': 15.6}], 'WR': [{'name': 'Chris Olave', 'number': 12, 'fp': 14.9}], 'TE': [{'name': 'Taysom Hill', 'number': 7, 'fp': 11.8}]}, 'NYG': {'QB': [{'name': 'Daniel Jones', 'number': 8, 'fp': 18.7}], 'RB': [{'name': 'Tyrone Tracy Jr.', 'number': 29, 'fp': 12.3}], 'WR': [{'name': 'Malik Nabers', 'number': 1, 'fp': 15.6}], 'TE': [{'name': 'Theo Johnson', 'number': 85, 'fp': 9.1}]}, 'NYJ': {'QB': [{'name': 'Aaron Rodgers', 'number': 8, 'fp': 21.6}], 'RB': [{'name': 'Breece Hall', 'number': 20, 'fp': 15.8}], 'WR': [{'name': 'Garrett Wilson', 'number': 5, 'fp': 16.4}], 'TE': [{'name': 'Tyler Conklin', 'number': 83, 'fp': 10.2}]}, 'PHI': {'QB': [{'name': 'Jalen Hurts', 'number': 1, 'fp': 25.2}], 'RB': [{'name': 'Saquon Barkley', 'number': 26, 'fp': 19.8}], 'WR': [{'name': 'A.J. Brown', 'number': 11, 'fp': 17.5}], 'TE': [{'name': 'Dallas Goedert', 'number': 88, 'fp': 13.5}]}, 'PIT': {'QB': [{'name': 'Russell Wilson', 'number': 3, 'fp': 20.9}], 'RB': [{'name': 'Najee Harris', 'number': 22, 'fp': 13.8}], 'WR': [{'name': 'George Pickens', 'number': 14, 'fp': 14.7}], 'TE': [{'name': 'Pat Freiermuth', 'number': 88, 'fp': 10.6}]}, 'SF': {'QB': [{'name': 'Brock Purdy', 'number': 13, 'fp': 22.5}], 'RB': [{'name': 'Christian McCaffrey', 'number': 23, 'fp': 18.5}], 'WR': [{'name': 'Deebo Samuel', 'number': 19, 'fp': 15.2}], 'TE': [{'name': 'George Kittle', 'number': 85, 'fp': 16.4}]}, 'SEA': {'QB': [{'name': 'Geno Smith', 'number': 7, 'fp': 21.3}], 'RB': [{'name': 'Kenneth Walker III', 'number': 9, 'fp': 14.9}], 'WR': [{'name': 'DK Metcalf', 'number': 14, 'fp': 15.8}], 'TE': [{'name': 'Noah Fant', 'number': 87, 'fp': 10.4}]}, 'TB': {'QB': [{'name': 'Baker Mayfield', 'number': 6, 'fp': 22.4}], 'RB': [{'name': 'Bucky Irving', 'number': 7, 'fp': 13.6}], 'WR': [{'name': 'Mike Evans', 'number': 13, 'fp': 16.7}], 'TE': [{'name': 'Cade Otton', 'number': 88, 'fp': 11.9}]}, 'TEN': {'QB': [{'name': 'Will Levis', 'number': 8, 'fp': 18.9}], 'RB': [{'name': 'Tony Pollard', 'number': 20, 'fp': 14.1}], 'WR': [{'name': 'Calvin Ridley', 'number': 0, 'fp': 13.4}], 'TE': [{'name': 'Chig Okonkwo', 'number': 85, 'fp': 9.8}]}, 'WAS': {'QB': [{'name': 'Jayden Daniels', 'number': 5, 'fp': 26.3}], 'RB': [{'name': 'Brian Robinson Jr.', 'number': 8, 'fp': 12.7}], 'WR': [{'name': 'Terry McLaurin', 'number': 17, 'fp': 15.8}], 'TE': [{'name': 'Zach Ertz', 'number': 86, 'fp': 10.5}]}}

def load_rosters_background():
    if roster_cache['loading']: return
    roster_cache['loading'] = True
    logger.info('Loading rosters...')
    try:
        from nflreadpy import load_rosters
        import pandas as pd
        from datetime import datetime
        rosters_df = load_rosters(2025)
        teams_data = {}
        for team_abbr in rosters_df['team'].unique():
            if pd.isna(team_abbr): continue
            team_players = rosters_df[rosters_df['team'] == team_abbr]
            teams_data[team_abbr] = {'QB': [], 'RB': [], 'WR': [], 'TE': []}
            for _, player in team_players.iterrows():
                position = player.get('position', '')
                if position in ['QB', 'RB', 'WR', 'TE']:
                    player_info = {'name': player.get('player_name', 'Unknown'), 'number': int(player.get('jersey_number', 0)) if pd.notna(player.get('jersey_number')) else 0, 'fp': round(15.0 + (hash(player.get('player_name', '')) % 100) / 10, 1)}
                    teams_data[team_abbr][position].append(player_info)
        roster_cache['data'] = teams_data
        roster_cache['last_updated'] = datetime.now().isoformat()
        logger.info(f'Loaded {len(teams_data)} teams')
    except Exception as e:
        logger.error(f'Error: {str(e)}')
        roster_cache['data'] = get_fallback_data()
    finally:
        roster_cache['loading'] = False

Thread(target=load_rosters_background, daemon=True).start()

@app.route('/api/health', methods=['GET'])
def health(): return jsonify({'status': 'ok', 'rosters_loaded': roster_cache['data'] is not None, 'last_updated': roster_cache['last_updated']}), 200

