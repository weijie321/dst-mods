-- 旧断言目前全部同步执行；显式调用并结束。新增异步断言必须用 TEST.After。
local loader = kleiloadlua(MODS_ROOT .. TEST.TargetMod .. "/dst_selftest.lua")
assert(type(loader) == "function", "cannot load Wanda baseline assertions")
setfenv(loader, getfenv(1))
local run = loader()
assert(type(run) == "function", "Wanda baseline must return a function")
run(TEST.Legacy)
TEST.Done("旺达同步基线断言完成")
