package states;

import lime.utils.Assets;
import mikolka.funkin.custom.mobile.MobileScaleMode;
import mikolka.vslice.ui.title.TitleState;
import flixel.input.keyboard.FlxKey;
import mikolka.vslice.ui.disclaimer.TextWarnings.FlashingState;
import mikolka.vslice.ui.disclaimer.TextWarnings.OutdatedState;
import mikolka.vslice.components.ScreenshotPlugin;

#if android
import mikolka.vslice.ui.disclaimer.WarningState;
import haxe.io.Path;
#end

class InitState extends MusicBeatState
{
    public static var muteKeys:Array<FlxKey> = [FlxKey.ZERO];
	public static var volumeDownKeys:Array<FlxKey> = [FlxKey.NUMPADMINUS, FlxKey.MINUS];
	public static var volumeUpKeys:Array<FlxKey> = [FlxKey.NUMPADPLUS, FlxKey.PLUS];

    var mustUpdate:Bool = false;
	public static var updateAlreadyShown:Bool = false;
	public static var updateVersion:String = '';


	override function create()
	{
		super.create();

		persistentUpdate = true;
		persistentDraw = true;
		FlxG.mouse.visible = false;


		#if (cpp && windows)
		trace("Fixing DPI aware:");
		backend.Native.fixScaling();
		#end

		#if CHECK_FOR_UPDATES
		fetchUpdateData();
		#end

		trace("checking asset list cache");
		if(NativeFileSystem.openFlAssets?.length == 0){
			trace("Failed to load openflAssets during itit! Doing it now.");
			NativeFileSystem.openFlAssets = Assets.list();
		}

		trace("Loading game settings");
		ClientPrefs.loadPrefs();
		#if CHAPTER2_STANDALONE
		installBundledChapter2();
		#end

		trace("Loading translations");
		Language.reloadPhrases();

		trace("Setting some save related values");
		if (FlxG.save.data != null && FlxG.save.data.fullscreen)
		{
			FlxG.fullscreen = FlxG.save.data.fullscreen;
			// trace('LOADED FULLSCREEN SETTING!!');
		}
		if (FlxG.save.data.weekCompleted != null)
		{
			StoryMenuState.weekCompleted = FlxG.save.data.weekCompleted;
		}	

		
		FlxG.scaleMode = new MobileScaleMode(ClientPrefs.data.wideScreen); 
		
		#if TOUCH_CONTROLS_ALLOWED
		trace("Loading mobile data");
		MobileData.init();
		#end	

		trace("Init plugins:");
		//* FIRST INIT! iNITIALISE IMPORTED PLUGINS
		ScreenshotPlugin.initialize();
		#if android
		//* This is only for the 3.3 version
		var path = Path.join([lime.system.System.applicationStorageDirectory,backend.CoolUtil.getSavePath(),"funkin.sol"]);
		var exportPath = Path.join([mobile.backend.StorageUtil.StorageType.fromStr("EXTERNAL"),"funkin.sol"]);
		#if !OLD_SIGN_KEYS
		if(FileSystem.exists(exportPath) && FlxG.save.data.flashing == null){
			var txt = "Migration save data found!!!\n\n"+
			"Press A to import it\n";
			MusicBeatState.switchState(new WarningState(txt,() ->{
				FlxG.save.close();
				File.saveContent(path,File.getContent(exportPath));
				FileSystem.deleteFile(exportPath);
				Sys.exit(0);
			},null,new TitleState()));
		}else
		#end
		#end
		if (FlxG.save.data.flashing == null)
		{
			controls.isInSubstate = false;
			FlxTransitionableState.skipNextTransIn = true;
			FlxTransitionableState.skipNextTransOut = true;
			MusicBeatState.switchState(new FlashingState(new TitleState()));
		}
        else if (mustUpdate && !updateAlreadyShown){
			updateAlreadyShown = true;
            MusicBeatState.switchState(new OutdatedState(updateVersion,new TitleState()));
        }
		else
		{
			new FlxTimer().start(0.05, function(tmr:FlxTimer)
				{
					#if FREEPLAY
					MusicBeatState.switchState(new FreeplayState());
					#elseif CHARTING
					MusicBeatState.switchState(new ChartingState());
					#else
					MusicBeatState.switchState(new TitleState());
					#end
				});
		}
	}

	#if CHAPTER2_STANDALONE
	/**
	 * Standalone Android app: place the bundled Chapter 2 week/assets into this
	 * app's private data folder. P-Slice intentionally reads mods from its own
	 * filesystem, not from OpenFL's asset registry. No manual mod installation
	 * or all-files permission is needed.
	 */
	static function installBundledChapter2():Void
	{
		try
		{
			var assetPrefix = 'mods/tankman-chapter-2/';
			var root = StorageUtil.getStorageDirectory();
			var assets = Assets.list();
			var written = 0;
			for (assetPath in assets)
			{
				if (!assetPath.startsWith(assetPrefix) || assetPath.endsWith('/'))
					continue;
				var destination = root + assetPath;
				if (!FileSystem.exists(destination))
				{
					var data = Assets.getBytes(assetPath);
					if (data == null)
						continue;
					FileSystem.createDirectory(haxe.io.Path.directory(destination));
					File.saveBytes(destination, data);
					written++;
				}
			}
			if (FileSystem.exists(root + 'mods/tankman-chapter-2/pack.json'))
			{
				var listing = root + 'modsList.txt';
				var current = FileSystem.exists(listing) ? File.getContent(listing) : '';
				if (current.indexOf('tankman-chapter-2|1') < 0)
				{
					current = StringTools.replace(current, 'tankman-chapter-2|0', '');
					File.saveContent(listing, 'tankman-chapter-2|1' + (current.trim().length > 0 ? '\\n' + current.trim() : ''));
				}
				Mods.updatedOnState = false;
				Mods.pushGlobalMods();
				Mods.loadTopMod();
				trace('CHAPTER2_MOD_READY: ' + written + ' files extracted in app-private storage');
			}
			else
				trace('CHAPTER2_MOD_WARNING: packaged mod assets were not found');
		}
		catch (err:haxe.Exception)
		{
			trace('CHAPTER2_MOD_ERROR: ' + err.details());
		}
	}
	#end

	#if CHECK_FOR_UPDATES
	function fetchUpdateData()
	{
		if (ClientPrefs.data.checkForUpdates)
		{
			trace('checking for update');
			var http = new haxe.Http("https://raw.githubusercontent.com/mikolka9144/P-Slice/master/gitVersion.txt");

			http.onData = function(data:String)
			{
				updateVersion = data.split('\n')[0].trim();
				var curVersion:String = MainMenuState.pSliceVersion.trim();
				trace('version online: ' + updateVersion + ', your version: ' + curVersion);
				if (updateVersion != curVersion)
				{
					trace('versions arent matching!');
					mustUpdate = true;
				}
			}

			http.onError = function(error)
			{
				trace('error: $error');
			}

			http.request();
		}
	}
	#end
}
