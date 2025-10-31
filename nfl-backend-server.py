# NFL Backend Server with full 32-team fallback data
import os
import threading
import time
import logging
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nfl-backend")

# Simple in-memory cache for roster data
roster_cache = {
    'data': None,
    'last_updated': None,
    'loading': False,
}


def get_fallback_data():
    """Fallback roster data for all 32 NFL teams (QB, RB, WR, TE)."""
    return {
        'ARI': {'QB': [{'name': 'Kyler Murray', 'number': 1, 'fp': 21.2}], 'RB': [{'name': 'James Conner', 'number': 6, 'fp': 12.0}], 'WR': [{'name': 'Marvin Harrison Jr.', 'number': 18, 'fp': 13.6}], 'TE': [{'name': 'Trey McBride', 'number': 85, 'fp': 11.7}]},
        'ATL': {'QB': [{'name': 'Kirk Cousins', 'number': 18, 'fp': 19.0}], 'RB': [{'name': 'Bijan Robinson', 'number': 7, 'fp': 17.5}], 'WR': [{'name': 'Drake London', 'number': 5, 'fp': 13.1}], 'TE': [{'name': 'Kyle Pitts', 'number': 8, 'fp': 9.6}]},
        'BAL': {'QB': [{'name': 'Lamar Jackson', 'number': 8, 'fp': 25.8}], 'RB': [{'name': 'Derrick Henry', 'number': 22, 'fp': 17.2}], 'WR': [{'name': 'Zay Flowers', 'number': 4, 'fp': 15.5}], 'TE': [{'name': 'Mark Andrews', 'number': 89, 'fp': 12.8}]},
        'BUF': {'QB': [{'name': 'Josh Allen', 'number': 17, 'fp': 23.5}], 'RB': [{'name': 'James Cook', 'number': 4, 'fp': 14.8}], 'WR': [{'name': 'Keon Coleman', 'number': 0, 'fp': 12.0}], 'TE': [{'name': 'Dalton Kincaid', 'number': 86, 'fp': 11.2}]},
        'CAR': {'QB': [{'name': 'Bryce Young', 'number': 9, 'fp': 14.6}], 'RB': [{'name': 'Jonathon Brooks', 'number': 0, 'fp': 11.2}], 'WR': [{'name': 'Diontae Johnson', 'number': 5, 'fp': 12.4}], 'TE': [{'name': 'Tommy Tremble', 'number': 82, 'fp': 6.8}]},
        'CHI': {'QB': [{'name': 'Caleb Williams', 'number': 18, 'fp': 17.8}], 'RB': [{'name': 'D’Andre Swift', 'number': 0, 'fp': 13.0}], 'WR': [{'name': 'DJ Moore', 'number': 2, 'fp': 15.3}], 'TE': [{'name': 'Cole Kmet', 'number': 85, 'fp': 10.0}]},
        'CIN': {'QB': [{'name': 'Joe Burrow', 'number': 9, 'fp': 21.0}], 'RB': [{'name': 'Zack Moss', 'number': 31, 'fp': 11.5}], 'WR': [{'name': 'Ja’Marr Chase', 'number': 1, 'fp': 18.2}], 'TE': [{'name': 'Mike Gesicki', 'number': 88, 'fp': 7.5}]},
        'CLE': {'QB': [{'name': 'Deshaun Watson', 'number': 4, 'fp': 18.1}], 'RB': [{'name': 'Nick Chubb', 'number': 24, 'fp': 16.0}], 'WR': [{'name': 'Amari Cooper', 'number': 2, 'fp': 14.1}], 'TE': [{'name': 'David Njoku', 'number': 85, 'fp': 10.9}]},
        'DAL': {'QB': [{'name': 'Dak Prescott', 'number': 4, 'fp': 22.0}], 'RB': [{'name': 'Ezekiel Elliott', 'number': 15, 'fp': 9.8}], 'WR': [{'name': 'CeeDee Lamb', 'number': 88, 'fp': 19.0}], 'TE': [{'name': 'Jake Ferguson', 'number': 87, 'fp': 9.8}]},
        'DEN': {'QB': [{'name': 'Bo Nix', 'number': 10, 'fp': 15.4}], 'RB': [{'name': 'Javonte Williams', 'number': 33, 'fp': 10.7}], 'WR': [{'name': 'Courtland Sutton', 'number': 14, 'fp': 12.2}], 'TE': [{'name': 'Adam Trautman', 'number': 82, 'fp': 5.5}]},
        'DET': {'QB': [{'name': 'Jared Goff', 'number': 16, 'fp': 19.2}], 'RB': [{'name': 'Jahmyr Gibbs', 'number': 26, 'fp': 17.0}], 'WR': [{'name': 'Amon-Ra St. Brown', 'number': 14, 'fp': 18.5}], 'TE': [{'name': 'Sam LaPorta', 'number': 87, 'fp': 12.3}]},
        'GB': {'QB': [{'name': 'Jordan Love', 'number': 10, 'fp': 18.9}], 'RB': [{'name': 'Josh Jacobs', 'number': 8, 'fp': 15.0}], 'WR': [{'name': 'Jayden Reed', 'number': 11, 'fp': 12.9}], 'TE': [{'name': 'Luke Musgrave', 'number': 88, 'fp': 7.4}]},
        'HOU': {'QB': [{'name': 'C.J. Stroud', 'number': 7, 'fp': 22.1}], 'RB': [{'name': 'Joe Mixon', 'number': 28, 'fp': 14.2}], 'WR': [{'name': 'Nico Collins', 'number': 12, 'fp': 15.6}], 'TE': [{'name': 'Dalton Schultz', 'number': 86, 'fp': 9.2}]},
        'IND': {'QB': [{'name': 'Anthony Richardson', 'number': 5, 'fp': 22.0}], 'RB': [{'name': 'Jonathan Taylor', 'number': 28, 'fp': 18.0}], 'WR': [{'name': 'Michael Pittman Jr.', 'number': 11, 'fp': 14.0}], 'TE': [{'name': 'Jelani Woods', 'number': 80, 'fp': 6.8}]},
        'JAX': {'QB': [{'name': 'Trevor Lawrence', 'number': 16, 'fp': 19.3}], 'RB': [{'name': 'Travis Etienne Jr.', 'number': 1, 'fp': 16.1}], 'WR': [{'name': 'Christian Kirk', 'number': 13, 'fp': 13.3}], 'TE': [{'name': 'Evan Engram', 'number': 17, 'fp': 10.6}]},
        'KC': {'QB': [{'name': 'Patrick Mahomes', 'number': 15, 'fp': 24.1}], 'RB': [{'name': 'Isiah Pacheco', 'number': 10, 'fp': 12.4}], 'WR': [{'name': 'Rashee Rice', 'number': 4, 'fp': 16.8}], 'TE': [{'name': 'Travis Kelce', 'number': 87, 'fp': 14.2}]},
        'LV': {'QB': [{'name': 'Aidan O’Connell', 'number': 12, 'fp': 13.2}], 'RB': [{'name': 'Zamir White', 'number': 35, 'fp': 10.4}], 'WR': [{'name': 'Davante Adams', 'number': 17, 'fp': 17.1}], 'TE': [{'name': 'Brock Bowers', 'number': 19, 'fp': 9.5}]},
        'LAC': {'QB': [{'name': 'Justin Herbert', 'number': 10, 'fp': 21.4}], 'RB': [{'name': 'Gus Edwards', 'number': 35, 'fp': 9.9}], 'WR': [{'name': 'Joshua Palmer', 'number': 5, 'fp': 11.0}], 'TE': [{'name': 'Will Dissly', 'number': 89, 'fp': 5.2}]},
        'LAR': {'QB': [{'name': 'Matthew Stafford', 'number': 9, 'fp': 19.1}], 'RB': [{'name': 'Kyren Williams', 'number': 23, 'fp': 17.3}], 'WR': [{'name': 'Puka Nacua', 'number': 17, 'fp': 17.6}], 'TE': [{'name': 'Tyler Higbee', 'number': 89, 'fp': 7.3}]},
        'MIA': {'QB': [{'name': 'Tua Tagovailoa', 'number': 1, 'fp': 21.0}], 'RB': [{'name': 'De’Von Achane', 'number': 28, 'fp': 16.5}], 'WR': [{'name': 'Tyreek Hill', 'number': 10, 'fp': 22.5}], 'TE': [{'name': 'Jonnu Smith', 'number': 81, 'fp': 6.4}]},
        'MIN': {'QB': [{'name': 'J.J. McCarthy', 'number': 9, 'fp': 15.0}], 'RB': [{'name': 'Aaron Jones', 'number': 33, 'fp': 13.2}], 'WR': [{'name': 'Justin Jefferson', 'number': 18, 'fp': 21.0}], 'TE': [{'name': 'T.J. Hockenson', 'number': 87, 'fp': 12.0}]},
        'NE': {'QB': [{'name': 'Jacoby Brissett', 'number': 14, 'fp': 13.0}], 'RB': [{'name': 'Rhamondre Stevenson', 'number': 38, 'fp': 14.0}], 'WR': [{'name': 'Ja’Lynn Polk', 'number': 1, 'fp': 10.5}], 'TE': [{'name': 'Hunter Henry', 'number': 85, 'fp': 8.7}]},
        'NO': {'QB': [{'name': 'Derek Carr', 'number': 4, 'fp': 17.0}], 'RB': [{'name': 'Alvin Kamara', 'number': 41, 'fp': 17.8}], 'WR': [{'name': 'Chris Olave', 'number': 12, 'fp': 16.0}], 'TE': [{'name': 'Juwan Johnson', 'number': 83, 'fp': 7.9}]},
        'NYG': {'QB': [{'name': 'Daniel Jones', 'number': 8, 'fp': 17.1}], 'RB': [{'name': 'Devin Singletary', 'number': 26, 'fp': 11.8}], 'WR': [{'name': 'Malik Nabers', 'number': 9, 'fp': 13.4}], 'TE': [{'name': 'Darren Waller', 'number': 12, 'fp': 9.1}]},
        'NYJ': {'QB': [{'name': 'Aaron Rodgers', 'number': 8, 'fp': 18.0}], 'RB': [{'name': 'Breece Hall', 'number': 20, 'fp': 17.2}], 'WR': [{'name': 'Garrett Wilson', 'number': 17, 'fp': 15.7}], 'TE': [{'name': 'Tyler Conklin', 'number': 83, 'fp': 7.0}]},
        'PHI': {'QB': [{'name': 'Jalen Hurts', 'number': 1, 'fp': 24.0}], 'RB': [{'name': 'Saquon Barkley', 'number': 26, 'fp': 18.2}], 'WR': [{'name': 'A.J. Brown', 'number': 11, 'fp': 19.4}], 'TE': [{'name': 'Dallas Goedert', 'number': 88, 'fp': 10.4}]},
        'PIT': {'QB': [{'name': 'Russell Wilson', 'number': 3, 'fp': 17.5}], 'RB': [{'name': 'Najee Harris', 'number': 22, 'fp': 12.3}], 'WR': [{'name': 'George Pickens', 'number': 14, 'fp': 13.8}], 'TE': [{'name': 'Pat Freiermuth', 'number': 88, 'fp': 9.0}]},
        'SF': {'QB': [{'name': 'Brock Purdy', 'number': 13, 'fp': 21.3}], 'RB': [{'name': 'Christian McCaffrey', 'number': 23, 'fp': 24.5}], 'WR': [{'name': 'Brandon Aiyuk', 'number': 11, 'fp': 16.5}], 'TE': [{'name': 'George Kittle', 'number': 85, 'fp': 13.0}]},
        'SEA': {'QB': [{'name': 'Geno Smith', 'number': 7, 'fp': 17.9}], 'RB': [{'name': 'Kenneth Walker III', 'number': 9, 'fp': 13.7}], 'WR': [{'name': 'DK Metcalf', 'number': 14, 'fp': 15.2}], 'TE': [{'name': 'Noah Fant', 'number': 87, 'fp': 6.8}]},
        'TB': {'QB': [{'name': 'Baker Mayfield', 'number': 6, 'fp': 17.0}], 'RB': [{'name': 'Rachaad White', 'number': 1, 'fp': 15.1}], 'WR': [{'name': 'Mike Evans', 'number': 13, 'fp': 16.4}], 'TE': [{'name': 'Cade Otton', 'number': 88, 'fp': 8.1}]},
        'TEN': {'QB': [{'name': 'Will Levis', 'number': 8, 'fp': 14.9}], 'RB': [{'name': 'Tony Pollard', 'number': 1, 'fp': 14.4}], 'WR': [{'name': 'Calvin Ridley', 'number': 0, 'fp': 13.7}], 'TE': [{'name': 'Tyjae Spears', 'number': 32, 'fp': 6.0}]},
        'WAS': {'QB': [{'name': 'Jayden Daniels', 'number': 5, 'fp': 17.0}], 'RB': [{'name': 'Brian Robinson Jr.', 'number': 8, 'fp': 12.9}], 'WR': [{'name': 'Terry McLaurin', 'number': 17, 'fp': 13.5}], 'TE': [{'name': 'Zach Ertz', 'number': 86, 'fp': 7.2}]},
    }


def load_rosters_background():
    try:
        roster_cache['loading'] = True
        # Simulate external fetch; replace with real data loader if available
        time.sleep(0.5)
        roster_cache['data'] = get_fallback_data()
        roster_cache['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.exception("Failed to load roster data: %s", e)
    finally:
        roster_cache['loading'] = False


# Kick off background load once at startup
threading.Thread(target=load_rosters_background, daemon=True).start()


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'rosters_loaded': roster_cache['data'] is not None,
        'last_updated': roster_cache['last_updated'],
    }), 200


@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = [
        {'abbr': 'ARI', 'name': 'Arizona Cardinals'},
        {'abbr': 'ATL', 'name': 'Atlanta Falcons'},
        {'abbr': 'BAL', 'name': 'Baltimore Ravens'},
        {'abbr': 'BUF', 'name
