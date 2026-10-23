process REGISTRATION_CONVERT {
    tag "$meta.id"
    label 'process_single'

    container "freesurfer/freesurfer:7.4.1"
    containerOptions "--env FSLOUTPUTTYPE='NIFTI_GZ'"

    input:
    tuple val(meta), path(transformation), val(input_type), val(output_type), path(reference), path(affine_source), path(fs_license)

    output:
    tuple val(meta), path("*out_{affine,warp}.{nii,nii.gz,mgz,m3z,txt,lta,mat,dat}")    , emit: transformation
    path "versions.yml"                                                                 , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    def transform_types = [
        affine: [lta: "lta", fsl: "mat", mni: "xfm", reg: "dat", niftyreg: "txt", itk: "txt", vox: "txt"],
        warp: [m3z: "m3z", fsl: "nii.gz", lps: "nii.gz", itk: "nii.gz", ras: "nii.gz", vox: "mgz"]
    ]

    // Validation transformation type and coercion with conversion type
    def in_extension = transformation.name.tokenize('.')[1..-1].join('.')
    def transform_type = transform_types.affine.find{ it.value == in_extension } ? "affine" : "warp"
    if ( !transform_types[transform_type].containsKey(input_type) ) {
        error "Invalid input type for ${transform_type} transformation: ${input_type}."
    }
    if ( !transform_types[transform_type].containsKey(output_type) ) {
        error "Invalid output type for ${transform_type} transformation: ${output_type}."
    }

    def out_extension = transform_types[transform_type][output_type]
    def output_name = "${prefix}_out_${transform_type}.${out_extension}"
    def command = transform_type == "affine" ? "lta_convert" : "mri_warp_convert"

    if ( transform_type == "affine" ) {
        // Affine transformations are defined on the target space
        args += " --in$input_type $transformation --out$output_type $output_name --trg $reference"

        // Non-LTA inputs need source geometry, as does any conversion to LTA.
        if ( input_type != "lta" || output_type == "lta" ) {
            if ( !affine_source ) error "Source geometry (affine_source) must be provided to convert an affine from ${input_type} to ${output_type}."

            args += " --src $affine_source"
        }

        if ( task.ext.conform ) args += " --trgconform"
    }
    else {
        if ( input_type == output_type ) {
            error "Input and output warp transformation types must differ: ${input_type}."
        }
        // Deformable transformations are defined on the source space
        args += " --insrcgeom $reference --in$input_type $transformation --out$output_type $output_name"

        if ( task.ext.downsample ) args += " --downsample"
    }

    """
    export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=${task.ext.single_thread ? 1 : task.cpus}
    export OMP_NUM_THREADS=${task.ext.single_thread ? 1 : task.cpus}

    export FS_LICENSE=\$PWD/$fs_license

    $command $args

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        freesurfer: \$(mri_convert -version | grep "freesurfer" | sed -E 's/.* ([0-9.]+).*/\\1/')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def transform_types = [
        affine: [lta: "lta", fsl: "mat", mni: "xfm", reg: "dat", niftyreg: "txt", itk: "txt", vox: "txt"],
        warp: [m3z: "m3z", fsl: "nii.gz", lps: "nii.gz", itk: "nii.gz", ras: "nii.gz", vox: "mgz"]
    ]
    // Validation transformation type and coercion with conversion type
    def in_extension = transformation.name.tokenize('.')[1..-1].join('.')
    def transform_type = transform_types.affine.find{ it.value == in_extension } ? "affine" : "warp"
    if ( !transform_types[transform_type].containsKey(input_type) ) {
        error "Invalid input type for ${transform_type} transformation: ${input_type}."
    }
    if ( !transform_types[transform_type].containsKey(output_type) ) {
        error "Invalid output type for ${transform_type} transformation: ${output_type}."
    }

    if ( transform_type =="warp" ) {
        if ( input_type == output_type ) {
            error "Input and output transformation types must differ: ${input_type}."
        }
    }

    def out_extension = transform_types[transform_type][output_type]
    def output_name = "${prefix}_out_${transform_type}.${out_extension}"
    """
    set +e
    function handle_code () {
        local code=\$?
        ignore=( 1 )
        [[ " \${ignore[@]} " =~ " \$code " ]] || exit \$code
    }
    trap 'handle_code' ERR

    lta_convert --help
    mri_warp_convert --help

    touch $output_name

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        freesurfer: \$(mri_convert -version | grep "freesurfer" | sed -E 's/.* ([0-9.]+).*/\\1/')
    END_VERSIONS
    """
}
