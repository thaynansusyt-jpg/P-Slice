-- Chapter 2 PLUS: mission-status HUD. Lightweight: no update() loop or shaders.
-- Pairs with the WAR ROOM selection screen. Safe to enable on 4GB Android.
local missions = {
    ['redeploy'] = 'REDEPLOY / ARRIVAL',
    ['blackout'] = 'BLACKOUT / SIGNAL LOST',
    ['onslaught'] = 'ONSLAUGHT / CONTACT',
    ['warzone'] = 'WARZONE / HEAT',
    ['last-stand'] = 'LAST STAND / DEFENSE',
    ['no-more-heroes'] = 'NO MORE HEROES / FINAL',
    ['ugh-radio-remix'] = 'UGH RADIO / INTERCEPT'
}
local mission = 'CHAPTER 2 / LIVE FEED'
local active = false

function onCreatePost()
    local song = string.lower(songName or '')
    mission = missions[song] or mission
    makeLuaText('ch2Mission', 'WAR ROOM // '..mission, 680, 12, 22)
    setTextSize('ch2Mission', 15)
    setTextColor('ch2Mission', 'FBA268')
    setObjectCamera('ch2Mission', 'hud')
    setProperty('ch2Mission.alpha', 0.82)
    addLuaText('ch2Mission')

    makeLuaText('ch2Transmission', 'SIGNAL ONLINE', 250, 12, 46)
    setTextSize('ch2Transmission', 12)
    setTextColor('ch2Transmission', 'E4E9D4')
    setObjectCamera('ch2Transmission', 'hud')
    setProperty('ch2Transmission.alpha', 0.55)
    addLuaText('ch2Transmission')
    active = true
end

function onSongStart()
    if not active then return end
    -- Slight fade only on beginning. No oversized screen overlays.
    doTweenAlpha('ch2MissionFaded', 'ch2Mission', 0.42, 2.5, 'linear')
end

function onBeatHit()
    if not active then return end
    if curBeat % 16 == 0 then
        setTextString('ch2Transmission', 'SIGNAL // SYNC '..curBeat)
        setProperty('ch2Transmission.alpha', 0.78)
        doTweenAlpha('ch2SignalFaded', 'ch2Transmission', 0.3, 1.0, 'linear')
    end
end
