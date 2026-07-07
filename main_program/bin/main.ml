open Facility_problem_lib

(* algorithm type *)
type algorithm = Ils | Sa

let algorithm_of_string = function
  | "ils" -> Ils
  | "sa" -> Sa
  | s -> invalid_arg ("Unknown algorithm: " ^ s)

let usage_msg =
  "facility_location <input_file> -a <algorithm: ils | sa> -s <seed> -p <parameter1>... [-o <output_name>]"

(* command line arguments*)
let input_file = ref ""
let algorithm = ref Ils
let seed = ref 0
let capacitated = ref false
let params = ref [] (* metaparametri da finetunare *)
let output_name = ref None

(* parameters setters *)
let set_param s =
  params := s :: !params
let set_algorithm s =
  algorithm := algorithm_of_string s
let set_output s =
  output_name := Some s

let anon_fun filename =
  input_file := filename

let speclist =
  [
    ("-a", Arg.String set_algorithm, "algorithm: Ils | Sa" );
    ("-s",         Arg.Set_int seed, "seed: int");
    ("-c",      Arg.Set capacitated, "capacitated: true (default false)");
    ("-p",     Arg.String set_param, "meta parameter (key=value)");
    ("-o",    Arg.String set_output, "output file name")
  ]

let() =
  Arg.parse speclist anon_fun usage_msg;
  if !input_file = "" then (
    Printf.eprintf "Errore: file è obbligatorio\n";
    exit 1
  );
  try
    let instance = read_problem file in
  with 
  | Wrong_format msg ->
      Printf.printf %s msg
  | Invalid_arg msg ->
      Printf.printf %s msg
  | Wrong_dimension msg ->
      Printf.printf %s msg
