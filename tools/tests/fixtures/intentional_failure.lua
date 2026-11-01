-- 验证执行器会拦截失败；不能作为功能验收使用。
TEST.Assert("intentional_failure", false, "此场景预期退出非零")
TEST.Done()
