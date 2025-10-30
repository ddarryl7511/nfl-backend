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
