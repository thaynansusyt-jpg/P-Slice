-- Diagnostico visual da Semana L / Reboot para P-Slice Mobile.
-- INSTALACAO: copiar para mods/VsSenhorLaranja_PSlice_Teste/data/reboot-teste/laranja-debug.lua
-- NAO move a camera, nao altera personagens, nao muda o chart.
local accumulator = 0
local label = "SLR_CAMERA_DIAG"
local enabled = true
local debugLog = false -- alterar para true se quiser mensagens extras a cada 8 batidas

local function num(path)
    local ok, value = pcall(function() return getProperty(path) end)
    if not ok then return -9999 end
    return tonumber(value) or -9999
end

local function n(value)
    if value == -9999 then return "?" end
    return string.format("%.0f", value)
end

local function line()
    return "DIAG SLR | camera e personagens\n" ..
      "BF: x=" .. n(num("boyfriend.x")) .. " y=" .. n(num("boyfriend.y")) ..
      " h=" .. n(num("boyfriend.height")) .. "\n" ..
      "Laranja: x=" .. n(num("dad.x")) .. " y=" .. n(num("dad.y")) ..
      " h=" .. n(num("dad.height")) .. "\n" ..
      "Camera: scrollY=" .. n(num("camGame.scroll.y")) ..
      " alvoY=" .. n(num("camFollow.y")) ..
      " zoom=" .. string.format("%.2f", num("camGame.zoom")) .. "\n" ..
      "Secao=" .. tostring(curSection or "?") ..
      " segueBF=" .. tostring(mustHitSection)
end

function onCreatePost()
    if not enabled then return end
    makeLuaText(label, "Carregando diagnostico...", 670, 12, 157)
    setTextSize(label, 17)
    setTextAlignment(label, "left")
    setObjectCamera(label, "other")
    addLuaText(label)
    setProperty(label .. ".alpha", 0.95)
    -- Borda para leitura sobre qualquer fundo.
    setTextBorder(label, 2, "000000")
end

function onUpdatePost(elapsed)
    if not enabled then return end
    accumulator = accumulator + (tonumber(elapsed) or 0)
    if accumulator < 0.30 then return end
    accumulator = 0
    setTextString(label, line())
end

function onBeatHit()
    if debugLog and curBeat and curBeat % 8 == 0 then
        debugPrint(line())
    end
end
