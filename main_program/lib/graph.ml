open Instance

type edge = {
          dest: int;
   mutable cap: int;
          cost: int;
  mutable flow: int;
        rev_id: int; (* indice dell'arco residuo in adj.(dest) *)
}

(* solo per costruzione poi uso array di array perché più efficiente *)
type graph_builder = {
  n: int;
  adj_build: edge list ref array (* array: nodi, per ogni nodo: lista di edge uscenti *)
}

(* distanza all'inizio è +inf *)
type dist = Finite of int | Infinity

type graph = {
     n: int;
   adj: edge array array;  (* adj.(v) array di archi uscenti da v *)
  dist: dist array;       (* allocato una volta, riusato ad ogni Bellman-Ford *)
  pred: (int * int) option array;  (* (u, id)  per riconoscere edge da cui vengo*)
}

exception Too_much_flow of edge * int
exception Unreachable_node

let add_cost d cost =
  match d with
  | Infinity -> Infinity            (* Infinity + qualsiasi cosa = Infinity, sempre corretto *)
  | Finite x -> Finite (x + cost)

let (<<) d1 d2 =
  match d1, d2 with
  | Infinity, Infinity -> false
  | Infinity, Finite _ -> false
  | Finite _, Infinity -> true
  | Finite a, Finite b -> a < b

let add_edge g_build u v cap cost =
  let rev_id_u = List.length !(g_build.adj_build.(u)) in
  let rev_id_v = List.length !(g_build.adj_build.(v)) in
  let e_uv = { dest = v; cap; cost; flow = 0; rev_id = rev_id_v } in
  let e_vu = { dest = u; cap = 0; cost = -cost; flow = 0; rev_id = rev_id_u } in
  g_build.adj_build.(u) := e_uv :: !(g_build.adj_build.(u));
  g_build.adj_build.(v) := e_vu :: !(g_build.adj_build.(v))

(* edge source -> facility *)
let build_facility_edges g_build capacities =
  Array.iteri (fun i u -> (*indice e capacità*)
    add_edge g_build 0 (i+1) u 0
  ) capacities

let build_consumer_edges g_build demands first_costumer_id = 
  let sink = g_build.n - 1 in
  Array.iteri ( fun i d ->
    add_edge g_build (i+first_costumer_id) sink d 0
  ) demands

let infinity_cap demands =
  (* somma totale delle domande, o delle capacità facility:
     un limite che non può mai essere superato nella realtà del problema *)
  Array.fold_left (+) 0 demands

let build_shipment_edges g_build cost_matrix infinite_capacity =
  let consumer_fst_id = (Array.length cost_matrix) + 1 in
  Array.iteri ( fun i facility_cost ->
   Array.iteri ( fun j shipment_cost ->
     add_edge g_build (i+1) (consumer_fst_id+j) infinite_capacity shipment_cost
   ) facility_cost
  ) cost_matrix

let graph_of_builder builder =
  {
    n = builder.n;
    adj = Array.map ( fun adj_lst ->
      Array.of_list (List.rev !adj_lst)
    ) builder.adj_build;
    dist = Array.make builder.n Infinity;
    pred = Array.make builder.n None;
  }

let build_residual_graph instance =
  let n = instance.n + instance.m + 2 in (* sedi + acquirenti + source + sink *) 
  let capacities = Array.map Option.get instance.u in
  let infinite_capacity = infinity_cap instance.d in
  let g_builder = { n; adj_build = Array.init n (fun _ -> ref []) } in
  build_facility_edges g_builder capacities;
  build_shipment_edges g_builder instance.c infinite_capacity ;
  build_consumer_edges g_builder instance.d (instance.n + 1);
  graph_of_builder g_builder

(* restituisce false se non avviene una modifica per implementare early stopping *)
let relax g u du id e =  (* du distanza di u, id: id dell'edge in adj.(e.dest)*)
    let residual_cap = e.cap - e.flow in
      let candidate = Finite (du + e.cost) in
      if residual_cap > 0 && candidate << g.dist.(e.dest) then (
        g.dist.(e.dest) <- candidate;
        g.pred.(e.dest) <- Some (u, id);
        true
      )
      else false


(* rilassa tutti archi uscenti da u *)
let relax_out_u g u du out_edges =
  let has_changed = ref false in
  Array.iteri (fun id e ->
    if relax g u du id e then has_changed := true
  ) out_edges;
  !has_changed 

let relax_all g =
  let rec aux u has_changed =
    if u >= g.n then has_changed
    else
      let changed_here =
        match g.dist.(u) with
        | Infinity -> false
        | Finite du -> relax_out_u g u du g.adj.(u)
      in
      aux (u + 1) (has_changed || changed_here)
  in
  aux 0 false

(* Bellman-Ford per trovare cammino minimo *)
let bellman_ford g =
  (* inizializzo *)
  Array.fill g.dist 0 g.n Infinity;
  Array.fill g.pred 0 g.n None;
  g.dist.(0) <- Finite 0;

  let rec aux i =
    if i < g.n - 1 then 
      let changed = relax_all g in
      if changed = true then
        aux (i+1)
  in
  aux 0;

let find_shortest_path g =
  let sink = g.n -1 in
  let rec aux i acc = 
    if i > 0 then
      match g.pred.(i) with
      | None -> raise Unreachble_node
      | Some (u, id) -> aux u ((u,id)::acc)
    else
      acc
  in
  aux sink []

let add_flow g edge amount =
  let new_flow = edge.flow + amount in
  if new_flow > edge.cap then
    raise (Too_much_flow (edge, amount))
  else begin
    edge.flow <- new_flow;
    let e_rev = g.adj.(edge.dest).(edge.rev_id) in
    e_rev.flow <- e_rev.flow - amount
  end

let bottleneck g path =
  List.fold_left (fun acc (u, idx) ->
    let e = g.adj.(u).(idx) in
    min acc (e.cap - e.flow)
  ) max_int path

let augment g path amount =
  List.iter (fun (u, idx) ->
    let e = g.adj.(u).(idx) in
    add_flow e amount
  ) path

let min_cost_flow g =
  let rec aux g =
    match g.dist.(g.n - 1) with 
    | Infinity -> ()
    | Finite ->
        let path = find_shortest_path g in
        let bottleneck = g path in
        augment g path bottleneck;
        aux g
  in
  aux (bellman_ford g)

let extract_shipments g n_facility m_customer =
  Array.init n_facility (fun i ->
    Array.init m_customer (fun j ->
      let e = g.adj.(i + 1).(j + 1) in  (* +1 per saltare il residuo verso source *)
      e.flow
    )
  )

let update_facility_capacities g capacities is_open_vector =
  Array.iteri (fun i is_open ->
    g.adj.(0).(i).cap <- if is_open then capacities.(i) else 0
  ) is_open_vector

let reset_flow g =
  Array.iter (fun out_edges ->
    Array.iter (fun e -> e.flow <- 0) out_edges
  ) g.adj

let open_facility facilities capacities g =
  Array.iteri (fun i is_open ->
    if is_open then
      adsa
    else
      close_facility i+1

  ) facilities

  let reset_graph_for_evaluation g capacities is_open_vector =
    reset_flow g;
    update_facility_capacities g capacities is_open_vector
