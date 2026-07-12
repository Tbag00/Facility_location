type cost = Finite of int | Infeasible

let (<<) a b =
  match a, b with
  | Finite x, Finite y -> x < y
  | Finite _, Infeasible -> true
  | Infeasible, Finite _ -> false
  | Infeasible, Infeasible -> false

let string_of_cost = function
  | Finite c -> string_of_int c
  | Infeasible -> "infeasible"
