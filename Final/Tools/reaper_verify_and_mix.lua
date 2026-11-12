-- Run with REAPER: reaper.exe ChinjuForest_Assets.rpp reaper_verify_and_mix.lua
local script_source = debug.getinfo(1, "S").source:sub(2)
local tools_directory = script_source:match("^(.*)[/\\][^/\\]+$")
local root = tools_directory:match("^(.*)[/\\][^/\\]+$"):gsub("\\", "/")

local function json_string(value)
  return '"' .. tostring(value):gsub("\\", "\\\\"):gsub('"', '\\"'):gsub("\n", "\\n") .. '"'
end

local source_records = {}
local source_passed = reaper.CountMediaItems(0) == 12
for index = 0, reaper.CountMediaItems(0) - 1 do
  local item = reaper.GetMediaItem(0, index)
  local take = reaper.GetActiveTake(item)
  local source = take and reaper.GetMediaItemTake_Source(take)
  local rate = source and reaper.GetMediaSourceSampleRate(source) or 0
  local channels = source and reaper.GetMediaSourceNumChannels(source) or 0
  local filename = source and reaper.GetMediaSourceFileName(source, "") or ""
  local duration = source and reaper.GetMediaSourceLength(source) or 0
  local passed = rate == 48000 and channels == 2 and duration > 0
  source_passed = source_passed and passed
  source_records[#source_records + 1] = string.format(
    '{"file":%s,"sample_rate":%d,"channels":%d,"source_duration":%.6f,"passed":%s}',
    json_string(filename), rate, channels, duration, tostring(passed)
  )
end
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
reaper.Main_SaveProject(0, false)

local evidence = assert(io.open(root .. "/Evidence/reaper_validation.json", "w"))
evidence:write('{"reaper_version":' .. json_string(reaper.GetAppVersion()) ..
  ',"asset_project_item_count":' .. reaper.CountMediaItems(0) ..
  ',"passed":' .. tostring(source_passed) .. ',"sources":[' .. table.concat(source_records, ",") .. "]}")
evidence:close()
if not source_passed then
  error("REAPER found offline or incorrectly formatted source media")
end

-- Open a dedicated tab for the soundscape, keeping the asset audition tab available.
reaper.Main_OnCommand(40859, 0)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "PROJECT_SRATE_USE", 1, true)
local tracks = {}

local function track(name, gain_db)
  reaper.InsertTrackAtIndex(reaper.CountTracks(0), true)
  local result = reaper.GetTrack(0, reaper.CountTracks(0) - 1)
  reaper.GetSetMediaTrackInfo_String(result, "P_NAME", name, true)
  reaper.SetMediaTrackInfo_Value(result, "D_VOL", 10 ^ (gain_db / 20))
  tracks[name] = result
  return result
end

local function add_item(destination, filename, position, length, gain_db, pan, loop)
  local item = reaper.AddMediaItemToTrack(destination)
  local take = reaper.AddTakeToMediaItem(item)
  local source = reaper.PCM_Source_CreateFromFile(root .. "/Assets/" .. filename .. ".wav")
  assert(source, "Cannot read source " .. filename)
  reaper.SetMediaItemTake_Source(take, source)
  reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", filename, true)
  reaper.SetMediaItemInfo_Value(item, "D_POSITION", position)
  reaper.SetMediaItemInfo_Value(item, "D_LENGTH", length)
  reaper.SetMediaItemInfo_Value(item, "B_LOOPSRC", loop and 1 or 0)
  reaper.SetMediaItemInfo_Value(item, "D_VOL", 10 ^ (gain_db / 20))
  reaper.SetMediaItemTakeInfo_Value(take, "D_PAN", pan)
  if loop then
    reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", 2)
    reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", 3)
  end
end

add_item(track("WindLeaves", -.5), "AMB_WindLeaves_Loop", 0, 90, 0, 0, true)
add_item(track("Insects", -3), "AMB_Insects_Loop", 0, 90, 0, 0, true)
add_item(track("Waterfall", -7), "AMB_Waterfall_Loop", 0, 90, 0, 0, true)
track("Birds", 0)
track("Rustles", 0)
track("Bells", 0)
local cues = {
  {9, "Birds", "SFX_Bird_01", 4, -12, -.55},
  {24, "Rustles", "SFX_Rustle_01", 4, -9, .5},
  {31, "Birds", "SFX_Bird_02", 4, -15, .65},
  {45, "Bells", "SFX_Bell_01", 10, -18, -.25},
  {56, "Rustles", "SFX_Rustle_02", 4, -12, -.7},
  {67, "Birds", "SFX_Bird_03", 4, -16, .2},
  {78, "Rustles", "SFX_Rustle_03", 4, -12, .6}
}
for _, cue in ipairs(cues) do
  add_item(tracks[cue[2]], cue[3], cue[1], cue[4], cue[5], cue[6], false)
end
reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", 0, true)
reaper.GetSetProjectInfo(0, "RENDER_STARTPOS", 0, true)
reaper.GetSetProjectInfo(0, "RENDER_ENDPOS", 90, true)
reaper.GetSetProjectInfo(0, "RENDER_SRATE", 48000, true)
reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", 2, true)
reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true)
reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT", "ZXZhdxgAAA==", true)
reaper.GetSetProjectInfo_String(0, "RENDER_FILE", root .. "/Preview", true)
reaper.GetSetProjectInfo_String(0, "RENDER_PATTERN", "ChinjuForest_REAPER_90s", true)
reaper.Main_SaveProjectEx(0, root .. "/Audio_Edit/ChinjuForest_Mix.rpp", 0)
reaper.UpdateArrange()
reaper.Main_OnCommand(41824, 0)
