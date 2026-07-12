exception File_exception of string
open Cost

(* nome del file dovrebbe contenere algoritmo metaparametri e seed *)
let create_csv name header =
  if Sys.file_exists name then
    raise (File_exception ("file already exists: " ^ name));

  let oc = Out_channel.open_gen [Open_creat; Open_wronly; Open_excl] 0o644 name in
  (try
     let csv_oc = Csv.to_channel oc in
     Csv.output_record csv_oc header;
     Csv.close_out csv_oc (* flusha il buffer di Csv e chiude oc *)
   with e ->
     Out_channel.close_noerr oc; (* oc non ancora chiuso: non credo sia necessario *)
     raise e)

let append_row file row =
  let oc = Out_channel.open_gen [Open_wronly; Open_append] 0o644 file in
  (try
     let csv_oc = Csv.to_channel oc in
     Csv.output_record csv_oc row;
     Csv.close_out csv_oc
   with e ->
     Out_channel.close_noerr oc;
     raise e)

let trace_logger ~file ~iteration ~current_cost ~best_cost =
  if not (Sys.file_exists file) then begin
    let header = ["iteration"; "current_cost"; "best_cost"] in
    create_csv file header
  end;

  let row = [
    string_of_int iteration;
    string_of_cost current_cost;
    string_of_cost best_cost
  ] in
  append_row file row

let string_of_facilities facs =
  String.concat ";" (
    List.mapi (fun i is_open ->
      Printf.sprintf "%d: %s" i (if is_open then "aperta" else "chiusa")
    ) facs
  )
  
let runs_logger ~file ~n ~m ~algorithm ~seed ~best_cost ~best_iteration ~total_iteration ~time ~facilities ~params_dict =
  let n_str               = string_of_int n in
  let m_str               = string_of_int m in
  let algorithm_str       = Algorithm.string_of_algorithm algorithm in
  let seed_str            = string_of_int seed in
  let best_cost_str       = string_of_cost best_cost in
  let best_iteration_str  = string_of_int best_iteration in
  let total_iteration_str = string_of_int total_iteration in
  let time_str            = string_of_float time in
  let facilities_str      = string_of_facilities facilities in
  if not (Sys.file_exists file) then begin
    let header = [
      "n";
      "m";
      "algorithm";
      "seed";
      "best_cost";
      "best_iteration";
      "total_iteration";
      "time";
      "facilities";
      "max_iterations"; "p_mut";        (* parametri ils *)
      "t0"; "t_end"; "alpha"; "new_low" (* parametri sa *)
    ]
    in create_csv file header
  end;
  let raw_row = [
    n_str;
    m_str;
    algorithm_str;
    seed_str;
    best_cost_str;
    best_iteration_str;
    total_iteration_str;
    time_str;
    facilities_str;
  ] in
  let row = match algorithm with
  | Algorithm.ILS ->
      let max_iter = List.assoc_opt "iterations" params_dict in
      let p_mut    = List.assoc_opt "p_mut" params_dict in begin

      match max_iter, p_mut with
      | Some max_iter, Some p_mut ->
          raw_row @ [max_iter; p_mut; ""; ""; ""; "";]
      | _, _ ->
           invalid_arg "Argomenti ILS nel file csv errati, serve: iterations (int) e p_mut (float)"
      end
  | Algorithm.SA ->
    let t0      = List.assoc_opt "t0" params_dict in
    let t_end   = List.assoc_opt "t_end" params_dict in
    let alpha   = List.assoc_opt "alpha" params_dict in
    let new_low = List.assoc_opt "new_low" params_dict in begin

    match t0, t_end, alpha, new_low with
    | Some t0, Some t_end, Some alpha, Some new_low ->
        raw_row @ [
          "";
          "";
          t0;
          t_end;
          alpha;
          new_low;
        ]
       | _, _, _, _ ->
           invalid_arg "Argomenti SA nel csv errati, serve: t0, t_end (float), alpha (float) e new_low (int)"
    end
  in
  append_row file row
