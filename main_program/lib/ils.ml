open Instance

let perturbation rng vector p_mut =
  let result = Array.copy vector in
  let rec aux i =
    if i < Array.length result then begin
      let z = Random.State.float rng 1.0 in
      if z < p_mut then
        result.(i) <- not result.(i);
      aux (i+1)
    end
  in
  aux 0;
  result  (* returno array modificato *)

let neighbors_of vector =
  let rec aux i accumulator =
    if i = Array.length vector then
      List.rev accumulator
    else 
      let i_neighbor = Array.copy vector in
      i_neighbor.(i) <- not i_neighbor.(i);
      aux (i+1) (i_neighbor :: accumulator) 
in aux 0 []


let best_neighbor (x0, f_x0) f = (* f: objective function *)
  let neighbors    = neighbors_of x0 in
  let f_neighbors  = List.map f neighbors in
  let f_graph      = List.combine neighbors f_neighbors in
  let rec aux best = function
    [] -> best
    | (x, fx) :: rest ->
        if fx < snd best then aux (x, fx) rest
        else aux best rest
  in aux (x0, f_x0) f_graph

let rec local_search (x0, f_x0) f = (* passo coppia invece che solo x0 per evitare ricalcoli *)
  let (best, f_best) = best_neighbor (x0, f_x0) f in
  if f_best < f_x0 then
    local_search (best, f_best) f
  else
    (x0, f_x0)

let iterated_search ~rng ~log ~iterations ~p_mut ~instance ~f =
  let x0 = Array.init instance.n (fun _ -> Random.State.bool rng) in
  let (x0, f_x0) = local_search (x0, f x0) f in
  let rec aux current f_current best_iter i =
    (match log with
     | Some file ->
         Csv_logger.trace_logger ~file ~iteration:i
           ~current_cost:f_current ~best_cost:f_current
     | None -> ());
    if i < iterations then
      let tmp = perturbation rng current p_mut in
      let (next, f_next) = local_search (tmp, f tmp) f in
      if f_next < f_current then
        aux next f_next (i + 1) (i + 1)
      else
        aux current f_current best_iter (i + 1)
    else
      (current, f_current, best_iter, iterations)
  in
  aux x0 f_x0 0 0
