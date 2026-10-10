package states;

import backend.Song;
import backend.WeekData;
import flixel.FlxG;
import flixel.FlxSprite;
import flixel.text.FlxText;
import flixel.util.FlxColor;
import mikolka.vslice.ui.MainMenuState;

/** Unique six-song front-end for the original Chapter 2 fan mod. */
class Chapter2MenuState extends MusicBeatState
{
    var titles:Array<String> = ["REDEPLOY", "BLACKOUT", "ONSLAUGHT", "WARZONE", "LAST STAND", "NO MORE HEROES"];
    var slugs:Array<String> = ["redeploy", "blackout", "onslaught", "warzone", "last-stand", "no-more-heroes"];
    var bpms:Array<Int> = [140, 155, 165, 170, 180, 190];
    var labels:Array<FlxText> = [];
    var selection:Int = 0;
    var help:FlxText;
    var locked:Bool = false;

    override function create()
    {
        super.create();
        var background = new FlxSprite().loadGraphic(Paths.image("chapter2/menu"));
        background.setGraphicSize(FlxG.width, FlxG.height);
        background.updateHitbox();
        add(background);
        for (i in 0...titles.length)
        {
            var lx = i < 3 ? 125 : 675;
            var ly = 276 + (i % 3) * 82;
            var label = new FlxText(lx, ly, 465, titles[i], 30);
            label.setFormat(Paths.font("vcr.ttf"), 30, FlxColor.WHITE, LEFT);
            add(label);
            labels.push(label);
        }
        help = new FlxText(116, FlxG.height - 106, FlxG.width - 232,
            "CHOOSE A TRACK - ARROWS / ACCEPT / BACK", 18);
        help.setFormat(Paths.font("vcr.ttf"), 18, 0xFFFFAA54, CENTER);
        add(help);
        refresh();
        #if TOUCH_CONTROLS_ALLOWED
        addTouchPad('UP_DOWN', 'A_B');
        #end
    }

    function refresh()
    {
        for (i in 0...labels.length)
        {
            labels[i].color = i == selection ? 0xFFFFA02A : FlxColor.WHITE;
            labels[i].text = (i == selection ? "> " : "  ") + titles[i] + "  / " + bpms[i] + " BPM";
        }
    }

    override function update(elapsed:Float)
    {
        if (!locked)
        {
            if (controls.UI_UP_P) change(-1);
            if (controls.UI_DOWN_P) change(1);
            if (controls.UI_LEFT_P || controls.UI_RIGHT_P) change(3);
            if (controls.BACK)
            {
                locked = true;
                MusicBeatState.switchState(new MainMenuState());
            }
            if (controls.ACCEPT) openTrack();
        }
        super.update(elapsed);
    }

    function change(delta:Int)
    {
        FlxG.sound.play(Paths.sound("scrollMenu"));
        selection = (selection + delta + titles.length) % titles.length;
        refresh();
    }

    function openTrack()
    {
        var weekID = "tankman-chapter-2";
        PlayState.isStoryMode = false;
        WeekData.reloadWeekFiles(false);
        var n = WeekData.weeksList.indexOf(weekID);
        if (n < 0)
        {
            help.text = "ENABLE THE CHAPTER 2 MOD FIRST!";
            return;
        }
        WeekData.setDirectoryFromWeek(WeekData.weeksLoaded.get(weekID));
        PlayState.storyWeek = n;
        PlayState.storyDifficulty = 1;
        PlayState.storyPlaylist = [titles[selection]];
        PlayState.SONG = Song.loadFromJson(slugs[selection], slugs[selection]);
        if (PlayState.SONG == null)
        {
            help.text = "MISSING SONG CHART. RUN ASSET GENERATOR.";
            return;
        }
        locked = true;
        FlxG.sound.play(Paths.sound("confirmMenu"));
        LoadingState.loadAndSwitchState(new PlayState(), true);
    }
}
