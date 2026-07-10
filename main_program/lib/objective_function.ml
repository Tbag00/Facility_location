open Instance
exception Infeasible_solution
exception Capacities

(* valida istanza: true se corretta *)
let validate instance =
  let cost_matrix_rows = Array.length instance.c in
  let cost_matrix_cols = if cost_matrix_rows = 0 then 0
  else
    Array.length instance.c.(0)
  in
  let valid_capacity = match instance.u with
  | None -> true
  | Some u -> Array.length u = instance.n
  in
  instance.n = Array.length instance.f &&
  instance.m = Array.length instance.d &&
  cost_matrix_rows = instance.n &&
  cost_matrix_cols = instance.m &&
  valid_capacity
  
(* prende istanza e restituisce funzione obiettivo corrispondente *)
let objective_function instance x =
  match instance.u with
  | None ->
      let correct_cost_mat =
        Array.map2
          (fun cost_row is_open ->
             if is_open then cost_row
             else Array.make (Array.length cost_row) max_int)
          instance.c x
      in
      let rec aux j acc =
        if j < instance.m then
          let costo_spedizione =
            Array.fold_left (fun best row -> min best row.(j)) max_int correct_cost_mat
          in
          if costo_spedizione = max_int then
            raise Infeasible_solution
          else
            aux (j + 1) (costo_spedizione * instance.d.(j) + acc)
        else
          acc
      in
      aux 0 0
  | Some u -> raise Capacities

