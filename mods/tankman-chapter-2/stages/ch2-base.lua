-- Original Chapter 2 base: generated PNG layers, no Week 7 assets copied.
function onCreate()
    makeLuaSprite('ch2sky', 'chapter2/sky', -700, -450)
    setScrollFactor('ch2sky', 0.1, 0.1)
    addLuaSprite('ch2sky', false)
    makeLuaSprite('ch2city', 'chapter2/city', -650, -230)
    setScrollFactor('ch2city', 0.55, 0.6)
    addLuaSprite('ch2city', false)
    makeLuaSprite('ch2ground', 'chapter2/ground', -700, 550)
    addLuaSprite('ch2ground', false)
    makeLuaSprite('ch2signal', 'chapter2/signal', 360, -220)
    setScrollFactor('ch2signal', 0.65, 0.65)
    setProperty('ch2signal.alpha', 0.45)
    addLuaSprite('ch2signal', false)
end
function onBeatHit()
    if curBeat % 4 == 0 then
        setProperty('ch2signal.alpha', 0.9)
        doTweenAlpha('ch2signalDim', 'ch2signal', 0.35, 0.45, 'quadOut')
    end
end
