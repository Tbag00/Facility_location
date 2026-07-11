(* algorithm type *)
type algorithm = ILS | SA

let algorithm_of_string = function
  | "ils" -> ILS
  | "sa" -> SA
  | s -> invalid_arg ("Unknown algorithm: " ^ s)

let string_of_algorithm = function
  | ILS -> "ils"
  | SA -> "sa"

