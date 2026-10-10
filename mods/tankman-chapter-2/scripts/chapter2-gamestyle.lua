-- Lightweight global in-song stylistic effect, runs only for this pack.
function onCreatePost()
    makeLuaText('ch2Brand', 'CHAPTER 2 // LIVE FROM THE FRONT', 500, 20, 16)
    setTextSize('ch2Brand', 16)
    setTextColor('ch2Brand', 'FF9B31')
    setObjectCamera('ch2Brand', 'hud')
    addLuaText('ch2Brand')
end
function onSongStart()
    doTweenAlpha('ch2BrandFade', 'ch2Brand', 0.3, 3, 'linear')
end
