local Context = {
    _stack = {},
}

function Context.Push(entry)
    Context._stack[#Context._stack + 1] = entry or {}
end

function Context.Pop()
    local index = #Context._stack
    if index == 0 then
        return nil
    end

    local entry = Context._stack[index]
    Context._stack[index] = nil
    return entry
end

function Context.Peek()
    return Context._stack[#Context._stack]
end

function Context.Snapshot()
    local snapshot = {}
    for index, value in ipairs(Context._stack) do
        snapshot[index] = value
    end
    return snapshot
end

function Context.HasParentAction(action)
    if type(action) ~= "string" or action == "" then
        return false
    end

    for index = #Context._stack - 1, 1, -1 do
        local entry = Context._stack[index]
        if type(entry) == "table" and entry.action == action then
            return true
        end
    end

    return false
end

return Context
