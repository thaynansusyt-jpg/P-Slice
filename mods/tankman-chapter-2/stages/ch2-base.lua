-- Chapter 2 PLUS stage: large existing texture coverage, not new giant textures.
-- Previous layers only covered the center of the stage; camera exposed black space.
-- Scale GPU sprites rather than generating a costly 4K/8K bitmap.
function onCreate()
    makeLuaSprite('ch2sky', 'chapter2/sky', -1900, -1200)
    scaleObject('ch2sky', 3.35, 3.20)
    setScrollFactor('ch2sky', 0.10, 0.10)
    addLuaSprite('ch2sky', false)

    makeLuaSprite('ch2city', 'chapter2/city', -1200, -820)
    scaleObject('ch2city', 2.40, 2.40)
    setScrollFactor('ch2city', 0.55, 0.60)
    addLuaSprite('ch2city', false)

    makeLuaSprite('ch2ground', 'chapter2/ground', -1200, 500)
    scaleObject('ch2ground', 2.45, 2.45)
    setScrollFactor('ch2ground', 1.0, 1.0)
    addLuaSprite('ch2ground', false)

    makeLuaSprite('ch2signal', 'chapter2/signal', 360, -220)
    setScrollFactor('ch2signal', 0.65, 0.65)
    setProperty('ch2signal.alpha', 0.38)
    addLuaSprite('ch2signal', false)
end

function onBeatHit()
    if curBeat % 8 == 0 then
        -- Reuse the same sprite; no new textures or per-frame allocations.
        setProperty('ch2signal.alpha', 0.8)
        doTweenAlpha('ch2signalDim', 'ch2signal', 0.30, 0.48, 'quadOut')
    end
end
