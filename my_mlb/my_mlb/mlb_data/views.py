from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from .models import Player, Team, TeamSeason, PlayerSeason

def mlb_data(request):
    # Home page
    return render(request, 'index.html')

@csrf_exempt
def player_search(request):
    return render(request, 'player_search.html')

@csrf_exempt
def player_search_results(request):
    q_name = request.POST.get('q_name')
    players = Player.objects.filter(name__icontains=q_name) if q_name else []
    return render(request, 'player_search_results.html', {
        'players': players,
        'q_name': q_name,
    })

@csrf_exempt
def player_details(request, player_id):
    player = Player.objects.get(player_id=player_id)
    player_seasons = player.seasons.all()

    teams_by_year = {}
    # build mapping year → [Team, …]
    for ts in TeamSeason.objects.filter(players=player):
        teams_by_year.setdefault(ts.year, []).append(ts.team)

    return render(request, 'player_details.html', {
        'player': player,
        'player_seasons': player_seasons,
        'teams_by_year': teams_by_year,
    })

@csrf_exempt
def team_search(request):
    return render(request, 'team_search.html')

@csrf_exempt
def team_search_results(request):
    q_name = request.POST.get('q_name')
    teams = Team.objects.filter(name__icontains=q_name) if q_name else []
    return render(request, 'team_search_results.html', {
        'teams': teams,
        'q_name': q_name,
    })

def team_details(request, team_id):
    team = Team.objects.get(pk=team_id)
    seasons = team.seasons.all().order_by('-year')
    return render(request, 'team_details.html', {
        'team': team,
        'seasons': seasons,
    })

def team_roster(request, team_id):
    team = Team.objects.get(pk=team_id)
    year = request.GET.get('year')
    roster = []

    if year:
        try:
            year_int = int(year)
            ts = TeamSeason.objects.get(team=team, year=year_int)
            # ts.players is the M2M to Player
            players = ts.players.all()
            # Now pick up their PlayerSeason rows for that year
            roster = PlayerSeason.objects.filter(
                player__in=players,
                year=year_int
            ).select_related('player')
        except (TeamSeason.DoesNotExist, ValueError):
            roster = []

    return render(request, 'team_roster.html', {
        'team': team,
        'year': year,
        'roster': roster,
    })
