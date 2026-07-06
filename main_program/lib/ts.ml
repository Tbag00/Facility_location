open Ils

(* se i aperto [chiuso] nelle precedenti tenure soluzioni  allora non puo' essere chiuso [aperto] nelle prossime tenure soluzioni *)

type tabu_list = {
  tabu_until: int array; 
  tenure: int
}

