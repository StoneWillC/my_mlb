from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Player, Team, TeamSeason, PlayerSeason

def mlb_data(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))

@csrf_exempt
def player_search(request):
    template = loader.get_template('player_search.html')
    return HttpResponse(template.render({}, request))

@csrf_exempt
def player_search_results(request):
    q_name = request.POST.get('q_name')
    players = Player.objects.filter(name__icontains=q_name) if q_name else []
    context = {'players': players, 'q_name': q_name}
    template = loader.get_template('player_search_results.html')
    return HttpResponse(template.render(context, request))

@csrf_exempt
def player_details(request, player_id):
    player = Player.objects.get(player_id=player_id)
    player_seasons = player.seasons.all()

    # Build a mapping: season_year -> list of Team objects that this player played for
    teams_by_year = {}
    # Assumes TeamSeason has a ManyToMany to Player (or through a join) named "players"
    for ts in TeamSeason.objects.filter(players=player):
        teams_by_year.setdefault(ts.year, []).append(ts.team)

    context = {
        'player': player,
        'player_seasons': player_seasons,
        'teams_by_year': teams_by_year,
    }
    template = loader.get_template('player_details.html')
    return HttpResponse(template.render(context, request))

@csrf_exempt
def team_search(request):
    template = loader.get_template('team_search.html')
    return HttpResponse(template.render({}, request))

@csrf_exempt
def team_search_results(request):
    q_name = request.POST.get('q_name')
    teams = Team.objects.filter(name__icontains=q_name) if q_name else []
    context = {'teams': teams, 'q_name': q_name}
    template = loader.get_template('team_search_results.html')
    return HttpResponse(template.render(context, request))

def team_details(request, team_id):
    team = Team.objects.get(pk=team_id)
    seasons = team.seasons.all().order_by('-year')
    context = {'team': team, 'seasons': seasons}
    template = loader.get_template('team_details.html')
    return HttpResponse(template.render(context, request))

def team_roster(request, team_id):
    year = request.GET.get('year')
    team = Team.objects.get(pk=team_id)
    team_season = team.seasons.filter(year=year).first()

    if not team_season:
        return render(request, 'error.html', {'message': 'Team season not found.'})

    players = team_season.players.all()

    player_seasons = PlayerSeason.objects.filter(player__in=players, year=year)

    return render(request, 'team_roster.html', {
        'team': team,
        'year': year,
        'player_seasons': player_seasons
    })

