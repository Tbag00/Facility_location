(* reader.mli *)

exception Wrong_format of string
exception Invalid_arg of string
exception Wrong_dimension of string

(** Legge un'istanza CFLP da file e la converte in Instance.t.
    Solleva Wrong_format se il file è malformato. *)
val read_problem : string -> Instance.t

(* parse_parameters lst applica il parsing "K=V" a ogni riga della lista,
   restituendo la lista di coppie (K, V);
   solleva Wrong_format se una riga non contiene esattamente un '=' *)
val parse_parameters : string list -> (string * string) list
