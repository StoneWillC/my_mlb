from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

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
    team = Team.objects.get(pk=team_id)
    year = request.GET.get('year')
    roster = []
    if year:
        roster = PlayerSeason.objects.filter(year=year, teamseason__team=team)
    context = {'team': team, 'year': year, 'roster': roster}
    template = loader.get_template('team_roster.html')
    return HttpResponse(template.render(context, request))

