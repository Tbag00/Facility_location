exception Wrong_format of string
exception Invalid_arg of string
exception Wrong_dimension of string

let parse_array line =
  String.split_on_char ',' line |> List.map int_of_string |> Array.of_list

let parse_matrix line =
  String.split_on_char ';' line |> List.map parse_array |> Array.of_list

let parse_line line =
  match String.split_on_char '=' line with
  | [key; value] -> (key, value)
  | _ -> raise (Wrong_format "stringa malformata: expected KEY=VALUE\n")   (* riga malformata, niente '=' o più di uno *)


let instance_of_capability capability : Instance.t  =
  (* Faccio delle variabili mutabili da inserire a fine parsing nel record *)
  let n = ref None in
  let m = ref None in
  let f = ref None in
  let d = ref None in
  let c = ref None in
  let u = ref None in

  let rec aux = function 
    | [] -> ()
    | ("NUMBER_FACILITIES", str) ::     rest -> n := Some (int_of_string str); aux rest;
    | ("NUMBER_COSTUMERS", str) ::      rest -> m := Some (int_of_string str); aux rest;
    | ("SHIPMENT_COSTS_MATRIX", str) :: rest -> c := Some (parse_matrix str);  aux rest;
    | ("DEMAND", str) ::                rest -> d := Some (parse_array str);   aux rest;
    | ("COST_TO_OPEN", str) ::          rest -> f := Some (parse_array str);   aux rest;
    | ("MAX_CAPACITY", str) ::          rest -> u := Some (parse_array str);   aux rest;
    | _ -> raise (Wrong_format "stringa malformata: controlla errori di battitura nelle key\n")
  in
  aux capability;
  match !n, !m, !f, !d, !c with
  | Some n, Some m, Some f, Some d, Some c -> {n; m; f; d; c; u=!u;}
  | _ -> raise (Wrong_format "mancano degli argomenti\n")

let parse_problem ic =
  let rec aux acc = 
    match In_channel.input_line ic with
    | Some line -> parse_line line :: acc
    | None -> List.rev acc
  in
  let capability = aux [] in
  instance_of_capability capability

let read_problem file = In_channel.with_open_text file parse_problem
