(* parametri: rng iterations p_mut instance obj_function *)
val iterated_search :
  Random.State.t -> int -> float -> Instance.t -> (bool array -> 'a) -> bool array
