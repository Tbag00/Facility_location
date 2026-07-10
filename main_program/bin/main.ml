open Facility_problem_lib

(* algorithm type *)
type algorithm = ILS | SA

let algorithm_of_string = function
  | "ils" -> ILS
  | "sa" -> SA
  | s -> invalid_arg ("Unknown algorithm: " ^ s)

let usage_msg =
  "facility_location <input_file> -a <algorithm: ils | sa> -s <seed> -p <parameter1>... [-o <output_name>]"

(* command line arguments*)
let input_file  = ref ""
let algorithm   = ref ILS
let seed        = ref 0
let capacitated = ref false
let params      = ref [] (* metaparametri da finetunare *)
let output_name = ref None

(* parameters setters *)
let set_param s =
  params      := s :: !params

let set_algorithm s =
  algorithm   := algorithm_of_string s

let set_output s =
  output_name := Some s

let anon_fun filename =
  input_file  := filename

let speclist =
  [
    ("-a", Arg.String set_algorithm, "algorithm: ILS | SA" );
    ("-s",         Arg.Set_int seed, "seed: int");
    ("-c",      Arg.Set capacitated, "capacitated: true (default false)");
    ("-p",     Arg.String set_param, "meta parameter (key=value)");
    ("-o",    Arg.String set_output, "output file name")
  ]

let run = rng instance f params_dict = function ->
  | ILS ->
      let iterations = List.assoc_opt "iterations" params_dict in
      let p_mut = List.assoc_opt "p_mut" params_dict in        
      match iterations, p_mut with
      | Some iter, Some p ->
          let iter = int_of_string iter in
          let p = float_of_string p in
          Ils.iterated_search rng iter p instance f
      | _, _ ->
          raise (Invalid_arg "Argomenti ILS: iterations (int) e p_mut (float)")



let () =
  Arg.parse speclist anon_fun usage_msg;
  if !input_file = "" then (
    Printf.eprintf "Errore: file è obbligatorio\n";
    exit 1
  );
  try (
    let instance = Reader.read_problem file in
    if Objective_function.validate instance = false then
      raise (Wrong_format "istanza non valida")
    let f = Objective_function.objective_function instance in
    let rng = Random.State.make [| !seed |] in
    let params_dict = Reader.parse_parameters params in
    match !algorithm with
  with 
  | Wrong_format msg ->
      Printf.printf %s msg
  | Invalid_arg msg ->
      Printf.printf %s msg
  | Wrong_dimension msg ->
      Printf.printf %s msg
