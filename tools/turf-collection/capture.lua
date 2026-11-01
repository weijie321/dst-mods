-- 仅用于离线读取指定模组的声明；不提供系统命令或来源文件写入能力。
local root, entry = arg[1], arg[2]
local hostio, hostload, hostdebug = io, load, debug
local function noop() end
local stub
stub = setmetatable({}, {__index=function() return stub end, __call=function() return stub end})
local function json(v)
    if type(v) == "string" then
        return '"' .. v:gsub('[%z\1-\31\\"]', function(c)
            return string.format('\\u%04x', string.byte(c))
        end) .. '"'
    elseif type(v) == "number" or type(v) == "boolean" then return tostring(v)
    elseif type(v) ~= "table" or v == stub then return "null" end
    local a, n, count = {}, #v, 0
    for _ in pairs(v) do count = count + 1 end
    if n > 0 and n == count then
        for i=1,n do a[i]=json(v[i]) end
        return '['..table.concat(a, ',')..']'
    end
    for k,val in pairs(v) do
        if type(k)=='string' then a[#a+1]=json(k)..':'..json(val) end
    end
    table.sort(a)
    return '{'..table.concat(a, ',')..'}'
end
local env = {}
for _, k in ipairs({'assert','error','ipairs','pairs','next','tonumber','tostring','type','select','pcall','xpcall','rawget','rawset','rawequal','setmetatable','getmetatable','string','table','math','utf8'}) do env[k]=_G[k] end
env.unpack=table.unpack
env.math.ldexp=function(x,n) return x * 2^n end
env.bit={band=function(a,b) return (a & b) & 0xffffffff end, bor=function(a,b) return (a | b) & 0xffffffff end,
    bxor=function(a,b,c) local v=a ~ b; if c then v=v ~ c end; return v & 0xffffffff end,
    lshift=function(a,n) return (a << n) & 0xffffffff end, rshift=function(a,n) return (a & 0xffffffff) >> n end,
    rol=function(a,n) return ((a << n) | ((a & 0xffffffff) >> (32-n))) & 0xffffffff end}
env.GLOBAL=env; env._G=env; env.env=env; env.MODROOT=root..'/'; env.modname='turf-extraction'
local function tree() return setmetatable({}, {__index=function(t,k) local v=tree(); rawset(t,k,v); return v end}) end
env.Assets={}; env.PrefabFiles={}; env.STRINGS=tree(); env.TUNING=stub
env.RGB=function(r,g,b) return {r/255,g/255,b/255,1} end
env.WORLD_TILES={GRASS=1,FOREST=2,DIRT=3,MARSH=4,ROCKY=5,SAVANNA=6,WOODFLOOR=7,FARMING_SOIL=8,CARPET=9,CARPET2=10,COTL_BRICK=11,OCEAN_ICE=12}
env.GROUND=env.WORLD_TILES; env.FALLOFF_IDS={}; env.TileGroups=nil
env.GetModConfigData=function() return nil end
env.print=noop; env.Asset=function(kind,file) return {type=kind,file=file} end
local records={}
env.AddTile=function(name,range,data,ground,mini,turf)
    records[#records+1]={name=name,range=range,data=data,ground=ground,mini=mini,turf=turf}
    env.WORLD_TILES[string.upper(name)]=100+#records
end
for _, k in ipairs({'ChangeTileRenderOrder','ChangeMiniMapTileRenderOrder','AddPrefabPostInit','AddSimPostInit','AddComponentPostInit','AddRoomPreInit','AddTaskPreInit','AddLevelPreInitAny','AddRoom','AddTask','AddFalloffTexture','AddMinimapAtlas','RegisterInventoryItemAtlas','AddRecipe2','AddRecipeFilter','AddClassPostConstruct','RegisterPrefabsImpl','RegisterSinglePrefab','AddPlayerPostInit','AddStategraphPostInit','AddModRPCHandler','AddClientModRPCHandler'}) do env[k]=noop end
env.Prefab=function() return stub end
env.TheSim=stub; env.TheWorld=stub; env.PREFABDEFINITIONS={}
env.package={loaded={},preload={},loaders={},searchers={}}
env.collectgarbage=noop
local function read(path)
    assert(not path:find('..',1,true),'不允许越过指定来源目录')
    local f=hostio.open(path,'rb'); if not f then return nil end
    local s=f:read('*a'); f:close()
    if s:sub(1,30):find('l_knm',1,true) or s:sub(1,1)=='\3' then
        s=s:reverse():gsub('.',function(c) return string.char((c:byte()+7)%256) end)
    end
    return s
end
local compiled=0
local function compile(s,name)
    -- 只取丰耘清单中的地皮表，避免执行同文件的农业、食物等系统。
    local turfs=s:match('(local TURF_LIST = %b{})')
    if turfs then s=turfs..'\nreturn {TURF_LIST=TURF_LIST}' end
    if arg[3] then
        compiled=compiled+1
        local f=assert(hostio.open(arg[3]..'/compiled-'..compiled..'.lua','wb'))
        f:write(s); f:close()
    end
    return hostload(s,name,'t',env)
end
env.loadstring=compile; env.load=compile
env.getfenv=function() return env end; env.setfenv=function(f) return f end
env.kleiloadlua=function(path)
    assert(path:sub(1,#root)==root,'只允许读取来源模组')
    local s=assert(read(path),'找不到文件 '..path)
    return assert(compile(s,'@'..path))
end
env.require=function(name)
    if env.package.loaded[name] then return env.package.loaded[name] end
    if env.package.preload[name] then
        local r=env.package.preload[name](name); env.package.loaded[name]=r or true; return r
    end
    local path=root..'/scripts/'..name..'.lua'
    local s=read(path)
    if s then
        local r=assert(compile(s,'@'..name))(); env.package.loaded[name]=r or true; return r
    end
    local ok,fn=pcall(env.kleiloadlua,path)
    if ok and type(fn)=='function' then
        local r=fn(); env.package.loaded[name]=r or true; return r
    end
    if name=='hmrmain/hmr_lists' then error('无法加载丰耘地皮清单: '..tostring(fn)) end
    return stub
end
env.modimport=function() end
setmetatable(env,{__index=function(_,k) return stub end})
local ticks=0
hostdebug.sethook(function() ticks=ticks+1; if ticks>100000 then error('声明读取超出指令预算') end end,'',10000)
local s=assert(read(entry),'找不到入口')
local ok,result=pcall(function() return assert(compile(s,'@'..entry))() end)
hostdebug.sethook()
if type(result)=='table' and result~=stub and result[1] and result[1].tile_name then
    for _,d in ipairs(result) do env.AddTile(d.tile_name,d.tile_range,d.tile_data,d.ground_tile_def,d.minimap_tile_def,d.turf_def) end
end
print(json({tiles=records,assets=env.Assets,ok=ok,error=not ok and tostring(result) or nil}))
