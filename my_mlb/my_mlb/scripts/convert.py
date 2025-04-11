import os
import sys
import django
import mysql.connector
import time
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_mlb.settings')
django.setup()

from mlb_data.models import Player, Position, PlayerSeason, BattingStats, FieldingStats, PitchingStats, CatchingStats, Team, TeamSeason

def connect_to_original_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="mlb_original"
    )

def add_positions(players):
    # First, ensure all positions exist in the new database
    positions = {
        'P': 'Pitcher',
        'C': 'Catcher',
        '1B': 'First Base',
        '2B': 'Second Base',
        '3B': 'Third Base',
        'SS': 'Shortstop',
        'OF': 'Outfield',
        'LF': 'Left Field',
        'CF': 'Center Field',
        'RF': 'Right Field',
        'DH': 'Designated Hitter'
    }
    
    for code in positions:
        Position.objects.get_or_create(position_code=code)
    
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT DISTINCT playerID, POS 
        FROM fielding 
        WHERE playerID IN (%s)
    """ % ','.join(['%s'] * len(players))
    cursor.execute(query, list(players.keys()))
    
    for row in cursor.fetchall():
        player = players[row['playerID']]
        try:
            position = Position.objects.get(position_code=row['POS'].strip())
            player.positions.add(position)
            print(f"Added position {position.position_code} to {player.name}")
        except Position.DoesNotExist:
            print(f"Position {row['POS']} not found for player {player.name}")
    
    cursor.close()
    conn.close()

def retrieve_players():
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    players = {}
    cursor.execute("""
        SELECT  playerId, 
                nameFirst, 
                nameLast, 
                nameGiven, 
                birthDay, 
                birthMonth, 
                birthYear, 
                deathDay, 
                deathMonth, 
                deathYear, 
                bats, 
                throws, 
                birthCity, 
                birthState, 
                birthCountry, 
                debut, 
                finalGame 
         FROM people
    """)
    
    for row in cursor.fetchall():
        pid = row['playerId']
        first_name = row['nameFirst']
        last_name = row['nameLast']
        if not pid or not first_name or not last_name:
            continue
        
        if row['birthYear'] is None:
            continue
        elif row['birthMonth'] is None or row['birthDay'] is None:
            birth_day = datetime(year=row['birthYear'], month=1, day=1)
        else:
            birth_day = datetime(year=row['birthYear'], month=row['birthMonth'], day=row['birthDay'])
        
        if row['deathYear'] is None:
            death_day = None
        elif row['deathMonth'] is None or row['deathDay'] is None:
            death_day = datetime(year=row['deathYear'], month=1, day=1)
        else:
            death_day = datetime(year=row['deathYear'], month=row['deathMonth'], day=row['deathDay'])
        
        first_game = datetime.strptime(row['debut'], '%Y-%m-%d').date() if row['debut'] else None
        last_game = datetime.strptime(row['finalGame'], '%Y-%m-%d').date() if row['finalGame'] else None
        
        player = Player.objects.create(
            name=first_name + " " + last_name,
            given_name=row['nameGiven'],
            birthdate=birth_day,
            deathdate=death_day,
            batting_hand=row['bats'],
            throwing_hand=row['throws'],
            birth_city=row['birthCity'],
            birth_state=row['birthState'],
            birth_country=row['birthCountry'],
            first_game=first_game,
            last_game=last_game
        )
        players[pid] = player
        print(f"Created player: {player.name}")
    
    cursor.close()
    conn.close()

    add_positions(players)
    return players

def add_seasons(players):
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT b.playerID, b.yearID, b.teamID, b.lgID,
               SUM(b.G) as gamesPlayed,
               SUM(s.salary) as totalSalary
        FROM batting b
        LEFT JOIN salaries s ON b.playerID = s.playerID AND b.yearID = s.yearID
        GROUP BY b.playerID, b.yearID, b.teamID, b.lgID
    """)
    
    for row in cursor.fetchall():
        pid = row['playerID']
        yid = row['yearID']
        p = players.get(pid)
        if p is None:
            continue

        ps = p.seasons.filter(year=yid).first()
        if ps is None:
            ps = PlayerSeason.objects.create(
                player=p,
                year=yid,
                games_played=row['gamesPlayed'],
                salary=row['totalSalary'] if row['totalSalary'] is not None else 0
            )
        else:
            ps.games_played += row['gamesPlayed']
            if row['totalSalary']:
                ps.salary += row['totalSalary']
            ps.save()
        print(f"Created player-season: {pid}, {yid}")
    
    cursor.close()
    conn.close()

def add_batting_stats(players):
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT playerID, yearID,
               SUM(AB) as atBats, 
               SUM(H) as hits, 
               SUM(2B) as doubles,
               SUM(3B) as triples, 
               SUM(HR) as homeRuns,
               SUM(RBI) as runsBattedIn, 
               SUM(SO) as strikeouts,
               SUM(BB) as walks, 
               SUM(HBP) as hitByPitch, 
               SUM(IBB) as intentionalWalks, 
               SUM(SB) as steals, 
               SUM(CS) as stealsAttempted
        FROM batting
        GROUP BY playerID, yearID
    """)
    
    for row in cursor.fetchall():
        pid = row['playerID']
        yid = row['yearID']
        p = players.get(pid)
        if p is None:
            continue
        ps = p.seasons.filter(year=yid).first()
        if ps:
            BattingStats.objects.create(
                player_season=ps,
                at_bats=row['atBats'],
                hits=row['hits'],
                doubles=row['doubles'],
                triples=row['triples'],
                home_runs=row['homeRuns'],
                runs_batted_in=row['runsBattedIn'],
                strikeouts=row['strikeouts'],
                walks=row['walks'],
                hits_by_pitch=row['hitByPitch'],
                intentional_walks=row['intentionalWalks'],
                steals=row['steals'],
                steals_attempted=row['stealsAttempted']
            )
            print(f"Added batting stats to {p.name}'s {yid} season")
    
    cursor.close()
    conn.close()

def add_fielding_stats(players):
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT playerID, yearID,
               SUM(E) as errors,
               SUM(PO) as putOuts,
               SUM(CASE WHEN POS = 'C' THEN PB ELSE 0 END) as passedBalls,
               SUM(CASE WHEN POS = 'C' THEN WP ELSE 0 END) as wildPitches,
               SUM(CASE WHEN POS = 'C' THEN SB ELSE 0 END) as stealsAllowed,
               SUM(CASE WHEN POS = 'C' THEN CS ELSE 0 END) as stealsCaught,
               MAX(CASE WHEN POS = 'C' THEN 1 ELSE 0 END) as isCatcher
        FROM fielding
        GROUP BY playerID, yearID
    """)
    
    for row in cursor.fetchall():
        pid = row['playerID']
        yid = row['yearID']
        p = players.get(pid)
        if p is None:
            continue
        
        ps = p.seasons.filter(year=yid).first()
        if ps:
            FieldingStats.objects.create(
                player_season=ps,
                errors=row['errors'],
                put_outs=row['putOuts']
            )
            print(f"Added fielding stats to {p.name}'s {yid} season")
    
            if row['isCatcher']:
                CatchingStats.objects.create(
                    player_season=ps,
                    passed_balls=row['passedBalls'],
                    wild_pitches=row['wildPitches'],
                    steals_allowed=row['stealsAllowed'],
                    steals_caught=row['stealsCaught']
                )
                print(f"Added catching stats to {p.name}'s {yid} season")
    
    cursor.close()
    conn.close()

def add_pitching_stats(players):
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT playerID, yearID,
               SUM(IPOuts) as outsPitched,
               SUM(ER) as earnedRunsAllowed, 
               SUM(HR) as homeRunsAllowed, 
               SUM(SO) as strikeouts, 
               SUM(BB) as walks, 
               SUM(W) as wins, 
               SUM(L) as losses, 
               SUM(WP) as wildPitches, 
               SUM(BFP) as battersFaced, 
               SUM(HBP) as hitBatters, 
               SUM(SV) as saves
        FROM pitching
        GROUP BY playerID, yearID
    """)
    
    for row in cursor.fetchall():
        pid = row['playerID']
        yid = row['yearID']
        p = players.get(pid)
        if p is None:
            continue
        ps = p.seasons.filter(year=yid).first()
        if ps:
            PitchingStats.objects.create(
                player_season=ps,
                outs_pitched=row['outsPitched'],
                earned_runs_allowed=row['earnedRunsAllowed'],
                home_runs_allowed=row['homeRunsAllowed'],
                strikeouts=row['strikeouts'],
                walks=row['walks'],
                wins=row['wins'],
                losses=row['losses'],
                wild_pitches=row['wildPitches'],
                batters_faced=row['battersFaced'],
                hit_batters=row['hitBatters'],
                saves=row['saves']
            )
            print(f"Added pitching stats to {p.name}'s {yid} season")
    
    cursor.close()
    conn.close()

def add_team_seasons():
    """
    Convert team data from the legacy database.
    This function calls the stored procedure sp_getTeamSeasons,
    then for each record, it creates or updates Team and TeamSeason
    objects.
    """
    conn = connect_to_original_db()
    cursor = conn.cursor(dictionary=True)
    
    # Call stored procedure to retrieve team-season data.
    cursor.callproc('sp_getTeamSeasons')
    
    for result in cursor.stored_results():
        for row in result.fetchall():
            team_code = row['teamID']
            season = row['yearID']
            wins = row['wins']
            losses = row['losses']
            team_name = row['teamName']
            
            # Get or create the Team. Use teamID as unique code.
            team, created = Team.objects.get_or_create(
                code=team_code,
                defaults={'name': team_name}
            )
            if not created and team.name != team_name:
                team.name = team_name
                team.save()
            
            # Create the TeamSeason instance.
            team_season, ts_created = TeamSeason.objects.get_or_create(
                team=team,
                season=season,
                defaults={'wins': wins, 'losses': losses}
            )
            if ts_created:
                print(f"Created TeamSeason: {team.name} ({season})")
            else:
                print(f"TeamSeason already exists: {team.name} ({season})")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    start_time = time.time()

    players = retrieve_players()
    add_seasons(players)
    add_batting_stats(players)
    add_fielding_stats(players)
    add_pitching_stats(players)
    
    # Convert team data using the stored procedure.
    add_team_seasons()
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Conversion took {duration:.2f} seconds")
