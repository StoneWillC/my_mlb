# Generated by Django 5.2 on 2025-04-24 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mlb_data', '0002_remove_player_team_seasons_remove_team_league_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playerseason',
            name='team_season',
        ),
        migrations.AddField(
            model_name='player',
            name='team_seasons',
            field=models.ManyToManyField(related_name='players', to='mlb_data.teamseason'),
        ),
        migrations.AddField(
            model_name='team',
            name='league',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='year_founded',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='year_last',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='teamseason',
            name='games',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
