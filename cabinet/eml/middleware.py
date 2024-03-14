def dalayed_action(action):
    def wrapper(*args,**kwargs):
        action.delay(*args,**kwargs)
        return "DONE"
    return wrapper


