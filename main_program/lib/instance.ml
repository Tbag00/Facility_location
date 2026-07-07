(* Type record of a Facility Location Problem *)

type t = {
  n: int; (* numero sedi *)
  m: int; (* numero clienti *)
  f: int array; (* costo apertura fabbriche *)
  d: int array; (* domanda cliente *)
  c: int array array; (* matrice costo spedizione *)
  u: int array option; (* capacita fabbriche ignorato nel caso capacitated=false *)
}
