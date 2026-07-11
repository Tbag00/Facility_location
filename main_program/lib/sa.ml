open Instance

let (%%) x y =  (* Modulo nativo ha anche numeri negativi *)
  let result = x mod y in
  if result >= 0 then
    result
  else
    result + y


let random_neighbor rng vector length =
  let result = Array.copy vector in
  let random_index = Random.State.int rng length in
  result.(random_index) <- not (result.(random_index));
  result


let accept_solution rng t f_old f_new = (* restituisce true se sceglie nuova soluzione *)
  let delta = f_new - f_old in
  if delta <= 0 then true
  else
    let p = exp (-. (float_of_int delta) /. t) in
    (Random.State.float rng 1.0) < p

let simulated_annealing ~log ~rng ~t0 ~t_end ~alpha ~new_low ~instance ~f =
  let s0 = Array.init instance.n (fun _ -> Random.State.bool rng) in
  let f_s0 = f s0 in
  let rec aux i (s, f_s) (best, f_best) best_iter t =
    (match log with
     | Some file ->
         Csv_logger.trace_logger ~file ~iteration:i
           ~current_cost:f_s ~best_cost:f_best
     | None -> ());
    if t < t_end then
      (best, f_best, best_iter, i - 1)
    else
      let next = random_neighbor rng s instance.n in
      let f_next = f next in
      let accepted = accept_solution rng t f_s f_next in
      let best, f_best, best_iter =
        if f_next < f_best then (next, f_next, i) else (best, f_best, best_iter)
      in
      let t = if i %% new_low = 0 then alpha *. t else t in
      if accepted then
        aux (i + 1) (next, f_next) (best, f_best) best_iter t
      else
        aux (i + 1) (s, f_s) (best, f_best) best_iter t
  in
  aux 1 (s0, f_s0) (s0, f_s0) 0 t0
