def aggregate(decisions):
    try:
        return decisions[0]['approved'] == 1
    except:
        return True
