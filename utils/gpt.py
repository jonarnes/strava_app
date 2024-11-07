import os
import requests

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from urllib.parse import urlencode
import json
from openai import OpenAI


from utils import manage_pg_db
from utils.strava_client import StravaClient

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

def test_gpt(athlete_id: int, activity_id: int):
    settings = manage_pg_db.get_settings(athlete_id)
    client = OpenAI()
    #export OPENAI_API_KEY="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"
    strava = StravaClient(athlete_id, activity_id)
    activity = strava.get_activity
    
    elapsed_time = timedelta(seconds=activity.get('elapsed_time', 0))
    time_pr_km = timedelta(seconds=activity.get('elapsed_time', 0)/(activity.get('distance')/1000))
    distance = activity.get('distance')/1000
    total_elevation_gain = activity.get('total_elevation_gain')
    sport_type = activity.get('sport_type')
    workout_type = activity.get('workout_type')
    achievement_count = activity.get('achievement_count')
    max_speed = activity.get('max_speed')
    average_speed = activity.get('average_speed')
    average_cadence = activity.get('average_cadence')
    average_watts = activity.get('average_watts')
    max_watts = activity.get('max_watts')
    max_heartrate = activity.get('max_heartrate')
    average_heartrate = activity.get('average_heartrate')
    suffer_score = activity.get('suffer_score','')
    calories = activity.get('calories','')
    gear = activity.get('gear',{}).get('name','')
    device = activity.get('device_name','')
    manual_activity = activity.get('manual', False)
    trainer = activity.get('trainer', False)

    bad_activities = "Elliptical,VirtualRide,VirtualRow,VirtualRun,EBikeRide,EMountainBikeRide"
    good_activities = "NordicSki,MountainBikeRide,TrailRun,BackcountrySki,NordicSki,Hike"

    settings = manage_pg_db.get_settings(athlete_id)
    language_prompt = " Skriv svaret på norsk."
    if settings.lan == "en":
        language_prompt =""

    coach_tone =f"""
    You're my coach. You're result oriented but motivating and you're pushing me hard. Your tone is sarcastic and tough but funny. You're often shouting.
    You give me feedback in the form of a short text message suited for social media. You may use slang, abbreviations and emoticons. You always compare my results and efforts to professional athletes' results and efforts expecting the same from me.
    You don't like activities of type {bad_activities}, becasue you think it's better to be out in nature, get wet and dirty and not needing electically powered aids.
    You are extatic about activities of type {good_activities}, becasue you like the outdoors, winter, snow, fresh air and mountaineering.
    However, make sure that the feedback is related to the actual activity ({sport_type}).
    Sometimes you may blame my equipment ({device},{gear}) questioning if I they're the reason for my performance.
    If there is information about "relative effort", you should know that higher number is better. An average score for an OK workout is 30. Higher than 50 should be appreciated.
    """
    if(manual_activity or trainer):
        coach_tone = coach_tone + " You don't trust manually entered activities! Ask for evidence, pictures, film or vitnesses! Leave the feedback with that and suggest a real workout next time."

    prompt = f"""
    Write a short feedback message evaluating my effort, max 300 characters, on my workout activity based on these data points:
    - activity type: {sport_type},
    - distance: {distance} km,
    - elapsed time: {elapsed_time} munites,
    - total elevation gain: {total_elevation_gain} meters,
    - max hart rate: {max_heartrate} bpm,
    - average hart rate: {average_heartrate} bpm,
    - calories spent: {calories},
    - max speed: {max_speed} km/h,
    - average speed: {average_speed} km/h,
    - time per kilometer: {time_pr_km} min/km,
    - manually entered activity: {manual_activity},
    - average cadence: {average_cadence},
    - max watts: {max_watts},
    - relative effort: {suffer_score}
    {language_prompt}
    """
    print(coach_tone)
    print(prompt)

    lead_text ="Melding fra 🤖Gjert:"

    description = activity.get('description')
    if lead_text in description:
        print(f'Coach for activity ID={activity_id} is already set.')
        return  # ok, but no processing

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": coach_tone},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    #print(json.dumps(activity))

    description = '' if description is None else description.rstrip() + '\n' + lead_text +"\n" + completion.choices[0].message.content


    payload = {'description': description }
    print('DESCRIPTION FOR STRAVA:', payload)
    strava.modify_activity(payload)
