open Facility_problem_lib

let usage_msg =
  "facility_location <input_file> -a <algorithm: ils | sa> -s <seed> -p <parameter1>... [-o <output_name>]"

(* command line arguments*)
let input_file  = ref ""
let algorithm   = ref Algorithm.ILS
let seed        = ref 0
let capacitated = ref false
let params      = ref [] (* metaparametri da finetunare *)
let output_name = ref None
let trace       = ref true

(* parameters setters *)
let set_param s =
  params := s :: !params

let set_algorithm s =
  algorithm := Algorithm.algorithm_of_string s

let set_output s =
  output_name := Some s

let anon_fun filename =
  input_file := filename

let speclist =
  [
    ("-a", Arg.String set_algorithm, "algorithm: ILS | SA" );
    ("-s",         Arg.Set_int seed, "seed: int");
    ("-c",      Arg.Set capacitated, "capacitated: true (default false)");
    ("-p",     Arg.String set_param, "meta parameter (key=value)");
    ("-o",    Arg.String set_output, "output file name");
    ("-notrace",   Arg.Clear trace,  "disabilita il trace log per-iterazione")
  ]

let run ~seed ~trace ~rng ~instance ~f ~params_dict ~algorithm =
  match algorithm with
  | Algorithm.ILS ->
      let iterations = List.assoc_opt "iterations" params_dict in
      let p_mut = List.assoc_opt "p_mut" params_dict in
      (match iterations, p_mut with
       | Some iter, Some p ->
           let iter_i = int_of_string iter in
           let p_f = float_of_string p in
           let log =
             if trace then
               Some (Printf.sprintf "trace_output/trace_ils_iter%d_pmut%s_seed%d.csv"
                       iter_i p seed)
             else None
           in
           Ils.iterated_search ~rng ~log ~iterations:iter_i ~p_mut:p_f ~instance ~f
       | _, _ ->
           invalid_arg "Argomenti ILS: iterations (int) e p_mut (float)")
  | Algorithm.SA ->
      let t0 = List.assoc_opt "t0" params_dict in
      let t_end = List.assoc_opt "t_end" params_dict in
      let alpha = List.assoc_opt "alpha" params_dict in
      let new_low = List.assoc_opt "new_low" params_dict in
      (match t0, t_end, alpha, new_low with
       | Some t0, Some t_end, Some alpha, Some new_low ->
           let t0_f = float_of_string t0 in
           let t_end_f = float_of_string t_end in
           let alpha_f = float_of_string alpha in
           let new_low_i = int_of_string new_low in
           let log =
             if trace then
               Some (Printf.sprintf "trace_output/trace_sa_t0%s_tend%s_alpha%s_newlow%s_seed%d.csv"
                       t0 t_end alpha new_low seed)
             else None
           in
           Sa.simulated_annealing ~log ~rng ~t0:t0_f ~t_end:t_end_f
             ~alpha:alpha_f ~new_low:new_low_i ~instance ~f
       | _, _, _, _ ->
           invalid_arg "Argomenti SA: t0, t_end (float), alpha (float) e new_low (int)")

let () =
  Arg.parse speclist anon_fun usage_msg;
  if !input_file = "" then begin
    Printf.eprintf "Errore: file è obbligatorio\n";
    exit 1
  end;
  try
    let instance = Reader.read_problem !input_file in
    if not (Objective_function.validate instance) then
      raise (Reader.Wrong_format "istanza non valida");
    let f = Objective_function.objective_function instance in
    let rng = Random.State.make [| !seed |] in
    let params_dict = Reader.parse_parameters !params in

    let start_time = Sys.time () in
    let (solution, f_solution, best_iteration, total_iteration) =
      run ~seed:!seed ~trace:!trace ~rng ~instance ~f
        ~params_dict ~algorithm:!algorithm
    in
    let elapsed_time = Sys.time () -. start_time in

    let cost_str = "Costo soluzione trovata: " ^ Cost.string_of_cost f_solution ^ "\n" in
    print_string cost_str;

    let output_name =
      match !output_name with
      | None -> "result"
      | Some str -> str
    in

    let runs_file = output_name ^ ".csv" in
    let facilities = Array.to_list solution in

    Csv_logger.runs_logger
      ~file:runs_file
      ~n:instance.n
      ~m:instance.m
      ~algorithm:!algorithm
      ~seed:!seed
      ~best_cost:f_solution
      ~best_iteration
      ~total_iteration
      ~time:elapsed_time
      ~facilities
      ~params_dict
  with
  | Reader.Wrong_format msg ->
      Printf.printf "%s\n" msg
  | Reader.Invalid_arg msg ->
      Printf.printf "%s\n" msg
  | Reader.Wrong_dimension msg ->
      Printf.printf "%s\n" msg
