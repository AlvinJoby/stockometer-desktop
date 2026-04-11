def validateInput(symbol):

    if not symbol:
        return {"status":False,"error":"symbol is required"}
    
    return {"status":True}