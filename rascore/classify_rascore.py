# -*- coding: utf-8 -*-

"""
Copyright (C) 2022 Mitchell Isaac Parker <mitch.isaac.parker@gmail.com>

This file is part of the rascore project.

The rascore project cannot be copied, edited, and/or distributed without the express
permission of Mitchell Isaac Parker <mitch.isaac.parker@gmail.com>.
"""

from .scripts import *
from .constants import *


def classify_rascore(coord_paths, out_path=None, num_cpu=1):

    if out_path is None:
        out_path = f"{os.getcwd()}/{rascore_str}_{classify_str}"

    cluster_path = f"{get_dir_path(dir_str=data_str, dir_path=get_dir_name(__file__))}/{rascore_str}_{cluster_str}"

    coord_path_lst = type_lst(coord_paths)

    if ".txt" in coord_path_lst[0]:
        df = load_table(coord_path_lst[0])
    else:
        df = pd.DataFrame()
        i = 0
        for coord_path in tqdm(
            coord_path_lst,
            desc="Loading coordinates",
            position=0,
            leave=True,
        ):
            structure = load_coord(coord_path)
            for model in structure:
                modelid = get_modelid(model)
                for chain in model:
                    chainid = get_chainid(chain)
                    df.at[i, core_path_col] = coord_path
                    df.at[i, modelid_col] = modelid
                    df.at[i, chainid_col] = chainid

    df_col_lst = list(df.columns)

    missing_col_lst = [
        x for x in [core_path_col, modelid_col, chainid_col] if x not in df_col_lst
    ]
    if len(missing_col_lst) > 0:
        print(f"Input table missing columns: {lst_to_str(missing_col_lst)}")

    else:
        if len([x for x in lig_col_lst if x not in df_col_lst]) > 0:
            df = annot_lig(
                df=df,
                site_dict=pharm_site_dict,
                match_dict=pharm_match_dict,
                num_cpu=num_cpu,
            )

        if pharm_class_col not in df_col_lst:
            for index in list(df.index.values):
                pharm_class = df.at[index, pharm_lig_site_col]
                if pharm_class not in [sp2_name, sp12_name, none_pharm_name]:
                    pharm_class = other_pharm_name
                df.at[index, pharm_class_col] = pharm_class

        if nuc_class_col not in df_col_lst:
            df[nuc_class_col] = df[bio_lig_col].map(nuc_class_dict).fillna(gtp_name)

        dih_dict = prep_dih(coord_paths, num_cpu=num_cpu)

        for loop_name, loop_resids in loop_resid_dict.items():

            cluster_loop_path = f"{cluster_path}/{loop_name}"
            classify_loop_path = f"{out_path}/{loop_name}"

            loop_result_df = pd.DataFrame()
            loop_sum_df = pd.DataFrame()
            loop_classify_report_df = pd.DataFrame()

            for nuc_class in nuc_class_lst:

                print(
                    f"Classifying {loop_name} conformations in {nuc_class} strructures."
                )

                loop_nuc_name = f"{loop_name}_{nuc_class}"

                cluster_table_path = get_file_path(
                    cluster_table_file,
                    dir_str=loop_nuc_name,
                    dir_path=cluster_loop_path,
                )

                fit_matrix_path = get_file_path(
                    fit_matrix_file, dir_str=loop_nuc_name, dir_path=cluster_loop_path
                )

                result_table_path = get_file_path(
                    result_table_file,
                    dir_str=loop_nuc_name,
                    dir_path=classify_loop_path,
                )

                sum_table_path = get_file_path(
                    sum_table_file, dir_str=loop_nuc_name, dir_path=classify_loop_path
                )

                classify_report_table_path = get_file_path(
                    classify_report_table_file,
                    dir_str=loop_nuc_name,
                    dir_path=classify_loop_path,
                )

                pred_matrix_path = get_file_path(
                    pred_matrix_file, dir_str=loop_nuc_name, dir_path=classify_loop_path
                )

                nuc_df = mask_equal(df, nuc_class_col, nuc_class)

                chi1_resids = None
                if loop_name == sw2_name:
                    chi1_resids = 71

                dih_df = build_dih_table(
                    df=nuc_df,
                    dih_dict=dih_dict,
                    bb_resids=loop_resids,
                    chi1_resids=chi1_resids,
                )

                cluster_df = load_table(cluster_table_path)

                build_dih_matrix(
                    fit_df=cluster_df,
                    pred_df=dih_df,
                    max_norm_path=pred_matrix_path,
                )

                fit_matrix = load_matrix(fit_matrix_path)
                pred_matrix = load_matrix(pred_matrix_path)

                classify_matrix(
                    cluster_df=cluster_df,
                    pred_df=dih_df,
                    fit_matrix=fit_matrix,
                    pred_matrix=pred_matrix,
                    result_table_path=result_table_path,
                    sum_table_path=sum_table_path,
                    report_table_path=classify_report_table_path,
                    max_nn_dist=0.45,
                    only_save_pred=True,
                    reorder_class=False,
                )

                result_df = load_table(result_table_path)
                sum_df = load_table(sum_table_path)
                classify_report_df = load_table(classify_report_table_path)

                result_df[loop_col] = loop_name
                sum_df[loop_col] = loop_name
                classify_report_df[loop_col] = loop_name

                result_df[nuc_class_col] = nuc_class
                sum_df[nuc_class_col] = nuc_class
                classify_report_df[nuc_class_col] = nuc_class

                loop_result_df = pd.concat([loop_result_df, result_df], sort=False)
                loop_sum_df = pd.concat([loop_sum_df, sum_df], sort=False)
                loop_classify_report_df = pd.concat(
                    [loop_classify_report_df, classify_report_df], sort=False
                )

            loop_result_df = loop_result_df.reset_index(drop=True)

            loop_sum_df = loop_sum_df.sort_values(
                by=[nuc_class_col, total_chain_col], ascending=[True, False]
            )

            loop_result_table_path = get_file_path(
                result_table_file, dir_str=loop_name, dir_path=out_path
            )
            loop_sum_table_path = get_file_path(
                sum_table_file, dir_str=loop_name, dir_path=out_path
            )
            loop_classify_report_table_path = get_file_path(
                classify_report_table_file,
                dir_str=loop_name,
                dir_path=out_path,
            )

            save_table(loop_result_table_path, loop_result_df)
            save_table(loop_sum_table_path, loop_sum_df)
            save_table(loop_classify_report_table_path, loop_classify_report_df)

            loop_result_df = loop_result_df.rename(columns={cluster_col: loop_name})

            loop_result_df = loop_result_df.loc[
                :, [core_path_col, modelid_col, chainid_col, loop_name]
            ]

            df = merge_tables([df, loop_result_df])

        if sw1_gtp_name in lst_col(df, sw1_name, unique=True):
            dist_df = build_dist_table(
                mask_equal(df, sw1_name, sw1_gtp_name),
                x_resids=[32],
                y_resids=[bio_lig_col],
                x_atomids=["OH"],
                y_atomids=[gtp_atomids],
                hb_status_col_lst=[hb_status_col],
                check_hb=True,
            )

            sw1_gtp_dict = make_dict(
                lst_col(dist_df, pdb_id_col), lst_col(dist_df, hb_status_col)
            )

            df[hb_status_col] = df[pdb_id_col].map(sw1_gtp_dict).fillna("")
            df[sw1_name].replace(
                {
                    sw1_gtp_name: "",
                    sw1_gtp_wat_name: "",
                    sw1_gtp_dir_name: "",
                    sw1_gtp_no_name: "",
                },
                inplace=True,
            )
            df[sw1_name] += df[hb_status_col].map(str)

            del df[hb_status_col]

        result_table_path = get_file_path(result_table_file, dir_path=out_path)

        save_table(result_table_path, df)

        for loop_name, loop_resids in loop_resid_dict.items():

            pymol_pml_path = get_file_path(
                f"{loop_name}_{pymol_pml_file}", dir_path=out_path
            )

            if loop_name == sw1_name:
                stick_resids = [32]
            elif loop_name == sw2_name:
                stick_resids = [71]

            write_pymol_script(
                df,
                pymol_pml_path,
                group_col=loop_name,
                stick_resids=stick_resids,
                loop_resids=loop_resids,
                style_ribbon=True,
                thick_bb=False,
                show_bio=True,
                color_palette=conf_color_dict[loop_name],
                sup_group=True,
                sup_resids=sup_resids,
                show_resids="1-166",
            )

    print("Rascore classification complete!")