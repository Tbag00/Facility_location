(* reader.mli *)

exception Wrong_format of string
exception Invalid_arg of string
exception Wrong_dimension of string

(** Legge un'istanza CFLP da file e la converte in Instance.t.
    Solleva Wrong_format se il file è malformato. *)
val read_problem : string -> Instance.t
