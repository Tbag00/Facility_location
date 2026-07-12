open Instance
open Cost

(* sollevata quando una soluzione non è ammissibile
   (nessuna facility aperta può servire un cliente) *)
exception Infeasible_solution

(* sollevata quando l'istanza ha capacità (instance.u = Some _),
   caso non gestito per ora *)
exception Capacities

(* valida istanza: true se corretta *)
val validate : t -> bool

(* prende istanza e restituisce funzione obiettivo corrispondente *)
val objective_function : t -> bool array -> cost
