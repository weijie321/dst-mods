-- Done 不能越过已经登记的异步断言；四秒后的失败也必须使执行器退出非零。
TEST.Assert("before_delayed_failure", true)
TEST.After(4, function()
    TEST.Assert("delayed_failure", false, "此场景预期失败")
end)
TEST.Done()
