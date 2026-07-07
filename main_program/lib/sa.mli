val simulated_annealing :
  Random.State.t ->
  float ->              (* t0 *)
  float ->              (* t_end *)
  float ->              (* alpha *)
  int ->                (* new_low *)
  Instance.t ->
  (bool array -> int) ->
  bool array * int
