package states;

import backend.Song;
import backend.WeekData;
import flixel.FlxG;
import flixel.FlxSprite;
import flixel.text.FlxText;
import flixel.util.FlxColor;
import mikolka.vslice.ui.MainMenuState;

/**
 * Chapter 2 radio console. Layout is proportional to the screen and remains
 * usable with keyboard, controller, mouse or Android touch controls.
 */
class Chapter2MenuState extends MusicBeatState
{
    var titles:Array<String> = ["REDEPLOY", "BLACKOUT", "ONSLAUGHT", "WARZONE", "LAST STAND", "NO MORE HEROES"];
    var slugs:Array<String> = ["redeploy", "blackout", "onslaught", "warzone", "last-stand", "no-more-heroes"];
    var bpms:Array<Int> = [140, 155, 165, 170, 180, 190];
    var rows:Array<FlxSprite> = [];
    var labels:Array<FlxText> = [];
    var selected:Int = 0;
    var details:FlxText;
    var status:FlxText;
    var playPanel:FlxSprite;
    var backPanel:FlxSprite;
    var busy:Bool = false;

    function textAt(x:Float, y:Float, width:Float, content:String, size:Int, color:FlxColor):FlxText
    {
        var t = new FlxText(x, y, width, content, size);
        t.setFormat(Paths.font("vcr.ttf"), size, color, LEFT);
        t.scrollFactor.set();
        add(t);
        return t;
    }

    function rectAt(x:Float,y:Float,width:Float,height:Float,color:FlxColor):FlxSprite
    {
        var s = new FlxSprite(x,y);
        s.makeGraphic(Std.int(Math.max(1,width)),Std.int(Math.max(1,height)),color);
        s.scrollFactor.set();
        add(s);
        return s;
    }

    override function create()
    {
        super.create();
        var w:Float = FlxG.width;
        var h:Float = FlxG.height;
        var bg = new FlxSprite().loadGraphic(Paths.image("chapter2/menu"));
        bg.setGraphicSize(Std.int(w),Std.int(h));
        bg.updateHitbox();
        bg.scrollFactor.set();
        add(bg);

        rectAt(0,0,w,h,0x65000000);
        rectAt(w*.055,h*.045,w*.89,h*.16,0xD90F121C);
        rectAt(w*.055,h*.202,w*.89,4,0xFFFF7029);
        var headingSize = Std.int(Math.max(25,Math.min(54,w*.044)));
        textAt(w*.075,h*.065,w*.83,"TANKMAN // CHAPTER 2",headingSize,0xFFFFC6A0);
        textAt(w*.075,h*.145,w*.80,"RADIO NETWORK   •   SIGNAL RESTORED",Std.int(Math.max(13,w*.016)),FlxColor.WHITE);

        var top:Float=h*.265;
        var gap:Float=h*.011;
        var rowHeight:Float=Math.min(h*.077,60);
        var rowWidth:Float=w*.49;
        var fontSize:Int=Std.int(Math.max(18,Math.min(30,w*.022)));
        for (i in 0...titles.length)
        {
            var y=top+i*(rowHeight+gap);
            var row=rectAt(w*.07,y,rowWidth,rowHeight,0xD91A1E29);
            rows.push(row);
            var t=textAt(w*.087,y+rowHeight*.19,rowWidth*.91,
                "0"+(i+1)+"  "+titles[i],fontSize,FlxColor.WHITE);
            labels.push(t);
        }

        var sideX=w*.60;
        rectAt(sideX,top,w*.33,h*.48,0xD9181B27);
        rectAt(sideX,top,w*.33,4,0xFFFF7029);
        textAt(sideX+w*.02,top+h*.035,w*.27,"NOW TRANSMITTING",Std.int(Math.max(15,w*.020)),0xFFFFA352);
        details=textAt(sideX+w*.02,top+h*.122,w*.29,"",Std.int(Math.max(15,w*.021)),FlxColor.WHITE);

        playPanel=rectAt(sideX+w*.016,top+h*.305,w*.29,h*.075,0xFFB94F20);
        textAt(sideX+w*.034,top+h*.319,w*.26,"PLAY SELECTED TRACK",Std.int(Math.max(16,w*.018)),FlxColor.WHITE);
        backPanel=rectAt(sideX+w*.016,top+h*.39,w*.29,h*.065,0xFF303542);
        textAt(sideX+w*.034,top+h*.401,w*.26,"RETURN TO MENU",Std.int(Math.max(15,w*.017)),FlxColor.WHITE);
        status=textAt(w*.075,h*.865,w*.83,"UP/DOWN: SELECT     ACCEPT/A: PLAY     BACK/B: EXIT",Std.int(Math.max(13,w*.014)),FlxColor.WHITE);
        refresh();

        #if TOUCH_CONTROLS_ALLOWED
        addTouchPad('UP_DOWN','A_B');
        #end
    }

    function refresh():Void
    {
        for (i in 0...rows.length)
        {
            rows[i].color=(i==selected) ? 0xFFFF772D : FlxColor.WHITE;
            rows[i].alpha=(i==selected) ? 1 : .83;
            labels[i].color=(i==selected) ? 0xFFFFFFFF : 0xFFDFE3EE;
        }
        details.text="FILE 0"+(selected+1)+" / 06\n\n"+titles[selected]+"\n"+bpms[selected]+" BPM\n\nBF vs TANKMAN\n\n[TEST BUILD]";
    }

    function shift(delta:Int):Void
    {
        selected=(selected+delta+titles.length)%titles.length;
        FlxG.sound.play(Paths.sound('scrollMenu'));
        refresh();
    }

    function exitMenu():Void
    {
        busy=true;
        MusicBeatState.switchState(new MainMenuState());
    }

    function checkClick():Void
    {
        #if mobile
        for (touch in FlxG.touches.list)
        {
            if (!touch.justPressed) continue;
            if (touch.overlaps(playPanel)) { launch(); return; }
            if (touch.overlaps(backPanel)) { exitMenu(); return; }
            for (i in 0...rows.length)
            {
                if (touch.overlaps(rows[i]))
                {
                    if (selected==i) launch(); else {selected=i;refresh();}
                    return;
                }
            }
        }
        #else
        if (FlxG.mouse.justPressed)
        {
            if (FlxG.mouse.overlaps(playPanel)) {launch();return;}
            if (FlxG.mouse.overlaps(backPanel)) {exitMenu();return;}
            for (i in 0...rows.length)
                if (FlxG.mouse.overlaps(rows[i]))
                {
                    if (selected==i) launch(); else {selected=i;refresh();}
                    return;
                }
        }
        #end
    }

    override function update(elapsed:Float)
    {
        if(!busy)
        {
            if(controls.UI_UP_P) shift(-1);
            if(controls.UI_DOWN_P) shift(1);
            if(controls.BACK) exitMenu();
            else if(controls.ACCEPT) launch();
            else checkClick();
        }
        super.update(elapsed);
    }

    function launch():Void
    {
        PlayState.isStoryMode=false;
        WeekData.reloadWeekFiles(false);
        var key="tankman-chapter-2";
        var week=WeekData.weeksList.indexOf(key);
        if(week<0)
        {
            status.text="ACTIVATE TANKMAN CHAPTER 2 IN MODS BEFORE PLAYING.";
            return;
        }
        WeekData.setDirectoryFromWeek(WeekData.weeksLoaded.get(key));
        PlayState.storyWeek=week;
        PlayState.storyDifficulty=1;
        PlayState.storyPlaylist=[titles[selected]];
        PlayState.SONG=Song.loadFromJson(slugs[selected],slugs[selected]);
        if(PlayState.SONG==null)
        {
            status.text="CHART MISSING! CHECK THE INSTALLED MOD FILES.";
            return;
        }
        busy=true;
        FlxG.sound.play(Paths.sound('confirmMenu'));
        LoadingState.loadAndSwitchState(new PlayState(),true);
    }
}
