let (%%) x y =  (* Modulo nativo ha anche numeri negativi *)
  let result = x mod y in
  if result >= 0 then
    result
  else
    result + y
;;

let random_neighbor rng vector length =
  let result = Array.copy vector in
  let random_index = (Random.State.int rng) %% length in
  result.(random_index) <- not (result.(random_index));
  result
;;

let accept_solution rng t f_old f_new = (* restituisce true se sceglie nuova soluzione *)
  let delta = f_new - f_old in
  if delta <= 0 then true
  else
    let p = exp (-. (float_of_int delta) /. t) in
    (Random.State.float rng 1.0) < p
;;

let simulated_annealing rng params instance f =
  let s0 = Array.init instance.n (fun _ -> Random.State.bool rng) in (* genera array dimensione n con bool a caso *)
  let aux i s f_s t =
    if t < params.t_end then
      s
    else
      let next = random_neighbor rng s params.n in
      let f_next = f next in
      let accepted = accept_solution rng t f_s f_next in
      let t = if i %% params.new_low then
        params.alpha .* t
      else
        t
      in if accepted then
        aux (i+1) next f_next t
      else
        aux (i+1) s f_s t
  in
  aux 1 s0 (f s0) params.t0
;;
