exception File_exception of string

val create_csv : string -> string list -> unit
val append_row : string -> string list -> unit

(* logger per ogni iterazione, va passata alla funzione ils o sa che scriveranno una riga ogni iter *)
val trace_logger :
  file:string -> iteration:int -> current_cost:Cost.cost -> best_cost:Cost.cost -> unit

(* logger di più run, quando si devono testare più metaparametri è utile per avere info riassuntive di più run *)
val runs_logger :
  file:string ->
  n:int ->
  m:int ->
  algorithm:Algorithm.algorithm ->
  seed:int ->
  best_cost:Cost.cost ->
  best_iteration:int ->
  total_iteration:int ->
  time:float ->
  facilities:bool list -> params_dict:(string * string) list -> unit
