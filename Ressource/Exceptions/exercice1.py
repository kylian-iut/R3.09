def divEntier(x: int, y: int) -> int:
    if x < y:
        return 0
    else:
        x = x - y
        return divEntier(x, y) + 1
if __name__=='__main__':
    try:
        x=int(input("x?"))
        y=int(input("y?"))
        resul=divEntier(x,y)
    except ValueError:
        print("La valeur saisie n'est pas un entier!")
    except RecursionError as err:
        if y == 0:
            print(f"Division par 0")
        elif x < 0 or y < 0:
            print(f"Une valeur saisie est négative!")
        else:
            print(f"Le programme ne s'est pas arrêté : {err}")
    else:
        print(resul)