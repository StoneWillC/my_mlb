from django.http import HttpResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from .models import Player, Team, TeamSeason
# Create your views here.
# Home page - Select team or player search
def mlb_data(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render())

# Player search page
@csrf_exempt
def player_search(request):
    template = loader.get_template('player_search.html')
    return HttpResponse(template.render())

# Player search results page
@csrf_exempt
def player_search_results(request): 
    q_name = request.POST.get('q_name')
    if q_name:
        players = Player.objects.filter(name__icontains=q_name)
    else:
        players = []
    template = loader.get_template('player_search_results.html')
    context = {
        'players': players,
        'q_name': q_name
    }
    return HttpResponse(template.render(context, request))

# Player details page
@csrf_exempt
def player_details(request, player_id):
    player = Player.objects.get(player_id=player_id)
    template = loader.get_template('player_details.html')
    context = {
        'player': player,
        'player_seasons': player.seasons.all()
    }
    return HttpResponse(template.render(context, request))

# # Team search page
@csrf_exempt
def team_search(request):
    template = loader.get_template('team_search.html')
    return HttpResponse(template.render())

# # Team search results page
@csrf_exempt
def team_search_results(request):
    q_name = request.POST.get('q_name')
    teams = Team.objects.filter(name__icontains=q_name) if q_name else []
    context = {'teams': teams, 'q_name': q_name}
    template = loader.get_template('team_search_results.html')
    return HttpResponse(template.render(context, request))

# # Team details page
def team_details(request, team_id):
    team = Team.objects.get(pk=team_id)
    seasons = team.seasons.all().order_by('-year')
    template = loader.get_template('team_details.html')
    context = {'team': team, 'seasons': seasons}
    return HttpResponse(template.render(context, request))

# # Team roster page
def team_roster(request, team_id):
    year = request.GET.get('year')
    team = Team.objects.get(pk=team_id)
    if year:
        roster = []
        # Find all players in that season by matching PlayerSeason.year
        from .models import PlayerSeason
        roster = PlayerSeason.objects.filter(year=year)
    else:
        roster = []
    template = loader.get_template('team_roster.html')
    context = {'team': team, 'year': year, 'roster': roster}
    return HttpResponse(template.render(context, request))
